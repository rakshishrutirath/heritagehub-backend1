from rest_framework import serializers
from .models import CanvasArtwork


class CanvasArtworkSerializer(serializers.ModelSerializer):

    class Meta:
        model = CanvasArtwork
        fields = [
            'id',
            'title',
            'template_image',
            'artwork_image',
            'created_at',
            'updated_at',
        ]

        read_only_fields = [
            'id',
            'created_at',
            'updated_at',
        ]