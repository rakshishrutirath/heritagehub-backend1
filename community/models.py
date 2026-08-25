from django.db import models
from django.conf import settings
from heritage.models import HeritageRecord

class VerificationLog(models.Model):
    ACTION_CHOICES = (
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
        ('correction_requested', 'Correction Requested'),
    )
    record = models.ForeignKey(HeritageRecord, on_delete=models.CASCADE, related_name='logs')
    reviewer = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    action = models.CharField(max_length=30, choices=ACTION_CHOICES)
    comment = models.TextField(blank=True, null=True)
    timestamp = models.DateTimeField(auto_now_add=True)