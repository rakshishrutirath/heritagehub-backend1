import json
import re
import time
import requests

from django.conf import settings


# =========================================================
# COMMON GEMINI REQUEST
# =========================================================

def _call_gemini(prompt, max_output_tokens=500):
    """
    Call the Google Generative Language API safely.

    Retries temporary provider errors:
    429 - Too Many Requests
    500 - Internal Server Error
    502 - Bad Gateway
    503 - Service Unavailable
    504 - Gateway Timeout
    """

    url = (
        "https://generativelanguage.googleapis.com/"
        f"v1beta/models/{settings.AI_MODEL_NAME}:generateContent"
    )

    headers = {
        "x-goog-api-key": settings.AI_API_KEY,
        "Content-Type": "application/json",
    }

    body = {
        "contents": [
            {
                "role": "user",
                "parts": [
                    {
                        "text": prompt
                    }
                ],
            }
        ],
        "generationConfig": {
            "maxOutputTokens": max_output_tokens,
            "temperature": 0.3,
        },
    }

    max_attempts = 3

    retryable_status_codes = {
        429,
        500,
        502,
        503,
        504,
    }

    last_error = ""

    for attempt in range(1, max_attempts + 1):
        try:
            response = requests.post(
                url,
                headers=headers,
                json=body,
                timeout=45,
            )

        except requests.exceptions.Timeout:
            last_error = "AI request timed out."

            if attempt < max_attempts:
                time.sleep(attempt * 2)
                continue

            return {
                "error": True,
                "code": 504,
                "detail": last_error,
            }

        except requests.exceptions.ConnectionError as exc:
            last_error = (
                "Could not connect to the AI service: "
                f"{str(exc)}"
            )

            if attempt < max_attempts:
                time.sleep(attempt * 2)
                continue

            return {
                "error": True,
                "code": 503,
                "detail": last_error,
            }

        except requests.exceptions.RequestException as exc:
            return {
                "error": True,
                "code": 502,
                "detail": (
                    "AI request failed: "
                    f"{str(exc)}"
                ),
            }

        # Successful HTTP response
        if response.status_code == 200:
            try:
                return {
                    "error": False,
                    "data": response.json(),
                }

            except ValueError:
                return {
                    "error": True,
                    "code": 502,
                    "detail": (
                        "AI service returned invalid JSON."
                    ),
                }

        last_error = (
            f"AI API returned {response.status_code}: "
            f"{response.text[:500]}"
        )

        # Retry temporary provider problems
        if (
            response.status_code in retryable_status_codes
            and attempt < max_attempts
        ):
            print(
                f"AI temporary error "
                f"{response.status_code}. "
                f"Retry {attempt}/{max_attempts}..."
            )

            time.sleep(attempt * 2)
            continue

        return {
            "error": True,
            "code": response.status_code,
            "detail": last_error,
        }

    return {
        "error": True,
        "code": 503,
        "detail": (
            last_error
            or "AI service is temporarily unavailable."
        ),
    }


# =========================================================
# EXTRACT MODEL TEXT
# =========================================================

def _extract_model_text(data):
    """
    Extract generated text from Gemini response.
    """

    try:
        candidates = data.get("candidates", [])

        if not candidates:
            return None

        content = candidates[0].get(
            "content",
            {},
        )

        parts = content.get(
            "parts",
            [],
        )

        if not parts:
            return None

        return parts[0].get(
            "text",
            "",
        ).strip()

    except (
        AttributeError,
        IndexError,
        TypeError,
    ):
        return None


# =========================================================
# CLEAN JSON RESPONSE
# =========================================================

def _parse_ai_json(raw_reply):
    """
    Parse JSON even if Gemini accidentally returns
    markdown fences or extra surrounding text.
    """

    if not raw_reply:
        return None

    cleaned = raw_reply.strip()

    # Remove ```json or ``` from beginning
    cleaned = re.sub(
        r"^```(?:json)?\s*",
        "",
        cleaned,
        flags=re.IGNORECASE,
    )

    # Remove ``` from end
    cleaned = re.sub(
        r"\s*```$",
        "",
        cleaned,
    )

    cleaned = cleaned.strip()

    # First try direct JSON parsing
    try:
        return json.loads(cleaned)

    except json.JSONDecodeError:
        pass

    # Fallback: locate JSON object
    match = re.search(
        r"\{.*\}",
        cleaned,
        re.DOTALL,
    )

    if not match:
        return None

    try:
        return json.loads(
            match.group(0)
        )

    except json.JSONDecodeError:
        return None


# =========================================================
# HERITAGE AI ASSISTANCE
# =========================================================

def get_ai_assistance(text):
    """
    Generate:
    - summary
    - tags
    - translation
    """

    text = (
        text
        or ""
    ).strip()

    if not text:
        return {
            "error": True,
            "code": 400,
            "detail": (
                "No heritage text was provided."
            ),
        }

    prompt = (
        "You are helping preserve cultural heritage.\n\n"
        "Given the community submission below, respond "
        "with ONLY one valid raw JSON object.\n"
        "Do not use markdown fences.\n"
        "Do not add explanations outside the JSON.\n\n"

        "The JSON must contain exactly these keys:\n\n"

        '"summary": A clear 2-sentence cultural heritage summary.\n'

        '"tags": A comma-separated string of relevant '
        "heritage keywords.\n"

        '"translation": If the submission is not in English, '
        "translate it naturally into English. "
        "If it is already English, repeat the original text.\n\n"

        "The submission may be written in English, Odia, "
        "Santali, Ho, Sambalpuri, or another Indian regional "
        "language.\n\n"

        f"Submission:\n{text}"
    )

    result = _call_gemini(
        prompt,
        max_output_tokens=500,
    )

    if result.get("error"):
        return result

    raw_reply = _extract_model_text(
        result["data"]
    )

    if not raw_reply:
        return {
            "error": True,
            "code": 502,
            "detail": (
                "AI response contained no usable content."
            ),
        }

    parsed = _parse_ai_json(
        raw_reply
    )

    if not parsed:
        return {
            "error": True,
            "code": 502,
            "detail": (
                "Could not parse the AI response as JSON."
            ),
            "raw": raw_reply[:500],
        }

    summary = str(
        parsed.get(
            "summary",
            "",
        )
    ).strip()

    tags = parsed.get(
        "tags",
        "",
    )

    if isinstance(
        tags,
        list,
    ):
        tags = ", ".join(
            str(tag).strip()
            for tag in tags
            if str(tag).strip()
        )

    else:
        tags = str(tags).strip()

    translation = str(
        parsed.get(
            "translation",
            "",
        )
    ).strip()

    return {
        "error": False,
        "summary": summary,
        "tags": tags,
        "translation": translation,
    }


# =========================================================
# ENGLISH -> ODIA TRANSLATION
# =========================================================

def translate_phrase_to_odia(english_text):
    """
    Translate an English phrase into Odia.
    """

    english_text = (
        english_text
        or ""
    ).strip()

    if not english_text:
        return {
            "error": True,
            "code": 400,
            "detail": (
                "No English phrase was provided."
            ),
        }

    prompt = (
        "Translate the following English phrase into "
        "natural and grammatically correct Odia script.\n\n"

        "Respond ONLY with the Odia translation.\n"
        "Do not add an explanation.\n"
        "Do not use markdown.\n"
        "Do not repeat the English sentence.\n\n"

        f"English phrase:\n{english_text}"
    )

    result = _call_gemini(
        prompt,
        max_output_tokens=400,
    )

    if result.get("error"):
        return result

    translated = _extract_model_text(
        result["data"]
    )

    if not translated:
        return {
            "error": True,
            "code": 502,
            "detail": (
                "AI response contained no usable translation."
            ),
        }

    translated = re.sub(
        r"^```(?:text)?\s*",
        "",
        translated.strip(),
        flags=re.IGNORECASE,
    )

    translated = re.sub(
        r"\s*```$",
        "",
        translated,
    ).strip()

    return {
        "error": False,
        "translated_text": translated,
    }
# =========================================================
# HERITAGEHUB FLOATING AI CHATBOT
# =========================================================

def chat_with_heritage_ai(
    message,
    language="english",
):
    """
    General HeritageHub conversational AI.

    Supports English and Odia.
    """

    message = (
        message
        or ""
    ).strip()

    language = (
        language
        or "english"
    ).strip().lower()

    if not message:
        return {
            "error": True,
            "code": 400,
            "detail": "No message was provided.",
        }

    # =====================================================
    # LANGUAGE
    # =====================================================

    is_odia = language in {
        "odia",
        "or",
        "ଓଡ଼ିଆ",
    }

    if is_odia:
        language_instruction = (
            "Reply only in natural Odia script. "
            "Do not reply in English except when a proper noun "
            "or technical term cannot be reasonably translated."
        )
    else:
        language_instruction = (
            "Reply in clear, natural English."
        )

    # =====================================================
    # PROMPT
    # =====================================================

    prompt = f"""
You are HeritageHub AI Assistant.

HeritageHub is a digital cultural heritage platform
focused mainly on Odisha, India.

You help users understand:

- Odisha heritage
- Jagannath culture
- temples and monuments
- Konark
- Udayagiri and Khandagiri
- Pattachitra
- Raghurajpur
- Odissi dance
- Sambalpuri dance
- Dhemsa
- traditional music
- tribal traditions
- folk art
- Dhokra craft
- palm-leaf art
- festivals
- Odisha food
- regional languages
- cultural preservation
- heritage villages
- historical places

You may also explain HeritageHub features such as:

- Explore
- Learn
- Contribute
- Community
- 3D Heritage
- Marketplace
- Canvas

Rules:

1. Be respectful toward cultures and communities.
2. Do not invent historical facts.
3. If uncertain, say the information should be verified.
4. Keep normal answers useful and reasonably concise.
5. Give more detail if the user asks for it.
6. {language_instruction}

User:
{message}
"""

    # =====================================================
    # CALL EXISTING GEMINI HELPER
    # =====================================================

    result = _call_gemini(
        prompt,
        max_output_tokens=700,
    )

    if result.get("error"):
        return result

    reply = _extract_model_text(
        result["data"]
    )

    if not reply:
        return {
            "error": True,
            "code": 502,
            "detail": (
                "AI response contained no usable content."
            ),
        }

    # =====================================================
    # CLEAN RESPONSE
    # =====================================================

    reply = re.sub(
        r"^```(?:text|markdown)?\s*",
        "",
        reply.strip(),
        flags=re.IGNORECASE,
    )

    reply = re.sub(
        r"\s*```$",
        "",
        reply,
    ).strip()

    return {
        "error": False,
        "reply": reply,
        "language": (
            "odia"
            if is_odia
            else "english"
        ),
    }