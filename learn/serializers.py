from rest_framework import serializers

from .models import (
    Song,
    DancePose,
    LanguagePhrase,
    RitualPractice,
)


# ============================================================
# SONG SERIALIZER
# ============================================================

class SongSerializer(serializers.ModelSerializer):
    audio = serializers.SerializerMethodField()

    class Meta:
        model = Song
        fields = [
            'id',
            'audio',
            'title',
            'genre',
            'artist',
            'region',
            'image',
            'youtube_url',
            'cloudinary_audio_url',
            'lyrics',
            'cultural_context',
            'created_at',
        ]

    def get_audio(self, obj):
        """
        Return Cloudinary URL when available.

        If Cloudinary URL is not available, use the
        Django backend media URL.

        This allows:
        - 15 songs -> Cloudinary
        - Hisid Halay Hoy -> backend media file
        """

        # 1. Use Cloudinary when available
        if obj.cloudinary_audio_url:
            return obj.cloudinary_audio_url

        # 2. Otherwise use the original backend file
        if obj.audio:
            request = self.context.get('request')

            if request:
                return request.build_absolute_uri(obj.audio.url)

            return obj.audio.url

        # 3. No audio available
        return None


# ============================================================
# DANCE POSE SERIALIZER
# ============================================================

class DancePoseSerializer(serializers.ModelSerializer):

    class Meta:
        model = DancePose
        fields = [
            'id',
            'dance_name',
            'pose_name',
            'image',
            'explanation',
            'tutorial_link',
            'order',
        ]


# ============================================================
# LANGUAGE PHRASE SERIALIZER
# ============================================================

class LanguagePhraseSerializer(serializers.ModelSerializer):

    class Meta:
        model = LanguagePhrase
        fields = [
            'id',
            'category',
            'english_phrase',
            'odia_translation',
            'audio',
        ]


# ============================================================
# RITUAL PRACTICE SERIALIZER
# ============================================================

class RitualPracticeSerializer(serializers.ModelSerializer):

    class Meta:
        model = RitualPractice
        fields = [
            'id',
            'title',
            'region',
            'description',
            'cultural_significance',
            'practices',
            'image',
            'created_at',
        ]