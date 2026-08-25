from rest_framework import serializers
from .models import Song, DancePose, LanguagePhrase


class SongSerializer(serializers.ModelSerializer):
    class Meta:
        model = Song
        fields = '__all__'


class DancePoseSerializer(serializers.ModelSerializer):
    class Meta:
        model = DancePose
        fields = '__all__'


class LanguagePhraseSerializer(serializers.ModelSerializer):
    class Meta:
        model = LanguagePhrase
        fields = '__all__'

from .models import RitualPractice 
class RitualPracticeSerializer(serializers.ModelSerializer):

    class Meta:
        model = RitualPractice
        fields = '__all__'