from rest_framework import serializers
from .models import VerificationLog

class VerificationLogSerializer(serializers.ModelSerializer):
    class Meta:
        model = VerificationLog
        fields = '__all__'
        read_only_fields = ['reviewer']
