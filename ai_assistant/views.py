from .services import chat_with_heritage_ai
from rest_framework.decorators import api_view
from rest_framework.response import Response
from heritage.models import HeritageRecord
from .services import get_ai_assistance

@api_view(['POST'])
def generate_ai_assistance(request, record_id):
    try:
        record = HeritageRecord.objects.get(id=record_id)
    except HeritageRecord.DoesNotExist:
        return Response({"status": "error", "detail": "Record not found"}, status=404)

    result = get_ai_assistance(record.description)

    if result["error"]:
        # The endpoint never crashes — it reports the problem cleanly instead,
        # so a live demo degrades gracefully rather than throwing a 500 error.
        return Response({"status": "ai_error", "detail": result["detail"]}, status=502)

    record.ai_summary = result["summary"]
    record.ai_tags = result["tags"]
    record.ai_translation = result["translation"]
    record.save()

    return Response({
        "status": "success",
        "ai_summary": record.ai_summary,
        "ai_tags": record.ai_tags,
        "ai_translation": record.ai_translation,
    })
@api_view(["POST"])
def heritage_ai_chat(request):
    message = (
        request.data.get("message", "")
        or ""
    ).strip()

    language = (
        request.data.get("language", "english")
        or "english"
    ).strip().lower()

    if not message:
        return Response(
            {
                "status": "error",
                "detail": "Message is required.",
            },
            status=400,
        )

    result = chat_with_heritage_ai(
        message=message,
        language=language,
    )

    if result.get("error"):
        return Response(
            {
                "status": "ai_error",
                "detail": result.get(
                    "detail",
                    "AI chat failed.",
                ),
            },
            status=result.get("code", 502),
        )

    return Response(
        {
            "status": "success",
            "reply": result.get("reply", ""),
            "language": result.get(
                "language",
                language,
            ),
        }
    )
