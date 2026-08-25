from rest_framework import viewsets, filters
from .models import Song, DancePose, LanguagePhrase, RitualPractice
from .serializers import SongSerializer, DancePoseSerializer, LanguagePhraseSerializer, RitualPracticeSerializer
from rest_framework.decorators import api_view
from rest_framework.response import Response
from ai_assistant.services import translate_phrase_to_odia

class SongViewSet(viewsets.ModelViewSet):
    queryset = Song.objects.all().order_by('title')
    serializer_class = SongSerializer
    filter_backends = [filters.SearchFilter]
    search_fields = ['title', 'artist', 'region']
    def get_queryset(self):
        queryset = super().get_queryset()
        genre = self.request.query_params.get('genre')
        if genre:
            queryset = queryset.filter(genre=genre)
        return queryset
    
class DancePoseViewSet(viewsets.ModelViewSet):
    queryset = DancePose.objects.all()
    serializer_class = DancePoseSerializer

    def get_queryset(self):
        queryset = super().get_queryset()
        dance_name = self.request.query_params.get('dance_name')
        if dance_name:
            queryset = queryset.filter(dance_name=dance_name)
        return queryset

class LanguagePhraseViewSet(viewsets.ModelViewSet):
    queryset = LanguagePhrase.objects.all()
    serializer_class = LanguagePhraseSerializer
    filter_backends = [filters.SearchFilter]
    search_fields = ['english_phrase', 'odia_translation']

    def get_queryset(self):
        queryset = super().get_queryset()
        category = self.request.query_params.get('category')
        if category:
            queryset = queryset.filter(category=category)
        return queryset

@api_view(['POST'])
def auto_translate_phrase(request):
    english_text = request.data.get('english_phrase', '').strip()

    if not english_text:
        return Response(
            {
                "status": "error",
                "detail": "english_phrase is required"
            },
            status=400
        )

    # Limit the phrase to maximum 8 words
    word_count = len(english_text.split())

    if word_count > 8:
        return Response(
            {
                "status": "error",
                "detail": "Please enter a short phrase of maximum 8 words."
            },
            status=400
        )

    result = translate_phrase_to_odia(english_text)

    if result["error"]:
        return Response(
            {
                "status": "ai_error",
                "detail": result["detail"]
            },
            status=502
        )

    return Response({
        "status": "success",
        "english_phrase": english_text,
        "odia_translation": result["translated_text"],
        "word_count": word_count
    })


@api_view(['GET'])
def ritual_practices(request):

    rituals = RitualPractice.objects.all()

    serializer = RitualPracticeSerializer(
        rituals,
        many=True,
        context={'request': request}
    )

    return Response(serializer.data)