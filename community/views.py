from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from heritage.models import HeritageRecord
from .models import VerificationLog

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def review_record(request, record_id):
    action = request.data.get('action')
    comment = request.data.get('comment', '')

    valid_actions = ['approved', 'rejected', 'correction_requested']
    if action not in valid_actions:
        return Response({"status": "error", "detail": f"action must be one of {valid_actions}"}, status=400)

    try:
        record = HeritageRecord.objects.get(id=record_id)
    except HeritageRecord.DoesNotExist:
        return Response({"status": "error", "detail": "Record not found"}, status=404)

    if action == 'approved':
        record.status = 'approved'
        record.verified_by = request.user
    elif action == 'rejected':
        record.status = 'rejected'

    record.save()
    VerificationLog.objects.create(record=record, reviewer=request.user, action=action, comment=comment)
    return Response({"status": "ok", "record_status": record.status})
