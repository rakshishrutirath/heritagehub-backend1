import base64
import mimetypes
import requests

from django.conf import settings


# ============================================================
# MESHY API URLS
# ============================================================

MESHY_CREATE_URL = (
    "https://api.meshy.ai/openapi/v1/image-to-3d"
)

MESHY_TASK_URL = (
    "https://api.meshy.ai/openapi/v1/image-to-3d/{}"
)


# ============================================================
# MAXIMUM GLB SIZE
# ============================================================

MAX_MODEL_SIZE = 10 * 1024 * 1024


# ============================================================
# IMAGE -> DATA URI
# ============================================================

def image_file_to_data_uri(image_field):
    """
    Convert a Django uploaded image into a base64
    data URI for Meshy.
    """

    mime_type, _ = mimetypes.guess_type(
        image_field.name
    )

    if not mime_type:
        mime_type = "image/jpeg"

    image_field.open("rb")

    try:
        image_bytes = image_field.read()
    finally:
        image_field.close()

    if not image_bytes:
        raise ValueError(
            "Uploaded image is empty."
        )

    encoded = base64.b64encode(
        image_bytes
    ).decode("utf-8")

    return f"data:{mime_type};base64,{encoded}"


# ============================================================
# GET MESHY API KEY
# ============================================================

def get_meshy_api_key():
    """
    Get the Meshy API key from Django settings.

    The key must start with 'msy_'.
    """

    api_key = getattr(
        settings,
        "MESHY_API_KEY",
        None
    )

    if not api_key:
        return {
            "error": True,
            "detail": (
                "Meshy API key is missing "
                "from Django settings."
            ),
        }

    api_key = str(api_key).strip()

    if not api_key:
        return {
            "error": True,
            "detail": (
                "Meshy API key is empty."
            ),
        }

    if not api_key.startswith("msy_"):
        return {
            "error": True,
            "detail": (
                "Invalid Meshy API key configuration. "
                "The Meshy key must start with 'msy_'."
            ),
        }

    return {
        "error": False,
        "key": api_key,
    }


# ============================================================
# CREATE MESHY IMAGE-TO-3D TASK
# ============================================================

def create_meshy_task(image_field):

    # --------------------------------------------------------
    # Get Meshy API key
    # --------------------------------------------------------

    key_result = get_meshy_api_key()

    if key_result.get("error"):
        return key_result

    api_key = key_result["key"]

    # --------------------------------------------------------
    # Convert uploaded image
    # --------------------------------------------------------

    try:
        image_data_uri = image_file_to_data_uri(
            image_field
        )

    except Exception as exc:
        return {
            "error": True,
            "detail": (
                "Could not read uploaded image: "
                f"{str(exc)}"
            ),
        }

    # --------------------------------------------------------
    # Headers
    # --------------------------------------------------------

    headers = {
        "Authorization": (
            f"Bearer {api_key}"
        ),
        "Content-Type": "application/json",
    }

    # ========================================================
    # MESHY REQUEST BODY
    # ========================================================

    body = {

        # Uploaded image as base64 data URI
        "image_url": image_data_uri,

        # Smart Topology
        "model_type": "smart-topology",

        # Meshy model
        "ai_model": "meshy-t2",

        # Keep polygon count reasonable
        "target_polycount": 4000,

        # Generate textures
        "should_texture": True,

        # Reasonable texture size
        "texture_resolution": "2k",

        # Only generate GLB
        "target_formats": [
            "glb"
        ],

        # Don't request additional PBR maps
        "enable_pbr": False,
    }

    # ========================================================
    # SEND REQUEST TO MESHY
    # ========================================================

    try:

        response = requests.post(
            MESHY_CREATE_URL,
            headers=headers,
            json=body,
            timeout=120,
        )

    except requests.RequestException as exc:

        return {
            "error": True,
            "detail": (
                "Could not connect to Meshy: "
                f"{str(exc)}"
            ),
        }

    # ========================================================
    # CHECK RESPONSE
    # ========================================================

    if response.status_code not in (
        200,
        201,
        202,
    ):

        return {
            "error": True,
            "detail": (
                f"Meshy returned "
                f"{response.status_code}: "
                f"{response.text[:1000]}"
            ),
        }

    # ========================================================
    # PARSE RESPONSE
    # ========================================================

    try:

        data = response.json()

    except ValueError:

        return {
            "error": True,
            "detail": (
                "Meshy returned an invalid "
                "JSON response."
            ),
        }

    # ========================================================
    # GET TASK ID
    # ========================================================

    task_id = data.get(
        "result"
    )

    if not task_id:

        return {
            "error": True,
            "detail": (
                "Meshy did not return "
                "a task ID."
            ),
        }

    # ========================================================
    # SUCCESS
    # ========================================================

    return {
        "error": False,
        "task_id": task_id,
    }


# ============================================================
# CHECK MESHY TASK STATUS
# ============================================================

def get_meshy_task(task_id):

    # --------------------------------------------------------
    # Validate task ID
    # --------------------------------------------------------

    if not task_id:

        return {
            "error": True,
            "detail": (
                "Meshy task ID is missing."
            ),
        }

    # --------------------------------------------------------
    # Get Meshy API key
    # --------------------------------------------------------

    key_result = get_meshy_api_key()

    if key_result.get("error"):
        return key_result

    api_key = key_result["key"]

    # --------------------------------------------------------
    # Headers
    # --------------------------------------------------------

    headers = {
        "Authorization": (
            f"Bearer {api_key}"
        ),
        "Content-Type": "application/json",
    }

    # --------------------------------------------------------
    # Task URL
    # --------------------------------------------------------

    url = MESHY_TASK_URL.format(
        task_id
    )

    # --------------------------------------------------------
    # Request status
    # --------------------------------------------------------

    try:

        response = requests.get(
            url,
            headers=headers,
            timeout=60,
        )

    except requests.RequestException as exc:

        return {
            "error": True,
            "detail": (
                "Could not connect to Meshy: "
                f"{str(exc)}"
            ),
        }

    # --------------------------------------------------------
    # Check status
    # --------------------------------------------------------

    if response.status_code != 200:

        return {
            "error": True,
            "detail": (
                f"Meshy returned "
                f"{response.status_code}: "
                f"{response.text[:1000]}"
            ),
        }

    # --------------------------------------------------------
    # Parse JSON
    # --------------------------------------------------------

    try:

        data = response.json()

    except ValueError:

        return {
            "error": True,
            "detail": (
                "Meshy returned invalid JSON."
            ),
        }

    # --------------------------------------------------------
    # Return result
    # --------------------------------------------------------

    return {
        "error": False,
        "data": data,
    }


# ============================================================
# DOWNLOAD GLB
# ============================================================

def download_glb(glb_url):
    """
    Download the generated GLB from Meshy.

    IMPORTANT:
    PythonAnywhere can use proxy environment variables.
    We disable environment proxy settings for this
    direct Meshy asset download.
    """

    # --------------------------------------------------------
    # Validate URL
    # --------------------------------------------------------

    if not glb_url:

        return {
            "error": True,
            "detail": (
                "GLB URL is missing."
            ),
        }

    # --------------------------------------------------------
    # Download GLB
    # --------------------------------------------------------

    response = None

    session = requests.Session()

    # IMPORTANT:
    # Do not inherit HTTP/HTTPS proxy settings from the
    # PythonAnywhere environment for the Meshy asset download.
    session.trust_env = False

    try:
        response = session.get(
            glb_url,
            timeout=180,
            stream=True,
        )

        response.raise_for_status()

    except requests.RequestException as exc:

        session.close()

        return {
            "error": True,
            "detail": (
                "Could not download GLB "
                "from Meshy: "
                f"{str(exc)}"
            ),
        }

    # --------------------------------------------------------
    # Read chunks
    # --------------------------------------------------------

    chunks = []

    total_size = 0

    try:

        for chunk in response.iter_content(
            chunk_size=1024 * 1024
        ):

            if not chunk:
                continue

            chunks.append(
                chunk
            )

            total_size += len(
                chunk
            )

            # ------------------------------------------------
            # Stop if file exceeds 10 MB
            # ------------------------------------------------

            if total_size > MAX_MODEL_SIZE:

                return {
                    "error": True,
                    "detail": (
                        "Meshy generated a GLB "
                        "larger than the 10 MB "
                        "storage limit. "
                        f"Current size: "
                        f"{total_size / (1024 * 1024):.2f} MB."
                    ),
                    "size": total_size,
                }

    finally:

        if response is not None:
            response.close()

        session.close()

    # --------------------------------------------------------
    # Combine chunks
    # --------------------------------------------------------

    content = b"".join(
        chunks
    )

    # --------------------------------------------------------
    # Final size check
    # --------------------------------------------------------

    if len(content) > MAX_MODEL_SIZE:

        return {
            "error": True,
            "detail": (
                "Generated GLB is larger "
                "than 10 MB. "
                f"Size: "
                f"{len(content) / (1024 * 1024):.2f} MB."
            ),
            "size": len(content),
        }

    # --------------------------------------------------------
    # Empty file check
    # --------------------------------------------------------

    if not content:

        return {
            "error": True,
            "detail": (
                "Meshy returned an "
                "empty GLB file."
            ),
            "size": 0,
        }

    # --------------------------------------------------------
    # Success
    # --------------------------------------------------------

    return {
        "error": False,
        "content": content,
        "size": len(content),
    }