from rest_framework import serializers
from .models import HeritageRecord, Category, Language, Location

class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = '__all__'

class LanguageSerializer(serializers.ModelSerializer):
    class Meta:
        model = Language
        fields = '__all__'

class LocationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Location
        fields = '__all__'

class HeritageRecordSerializer(serializers.ModelSerializer):
    class Meta:
        model = HeritageRecord
        fields = '__all__'
        read_only_fields = ['id', 'contributor', 'ai_summary', 'ai_tags', 'ai_translation', 'status', 'verified_by', 'qr_code', 'created_at']
        