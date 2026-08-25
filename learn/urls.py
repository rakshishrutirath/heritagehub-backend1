from django.urls import path
from rest_framework.routers import DefaultRouter
from .views import SongViewSet, DancePoseViewSet, LanguagePhraseViewSet, auto_translate_phrase, ritual_practices

router = DefaultRouter()
router.register('songs', SongViewSet)
router.register('dance-poses', DancePoseViewSet)
router.register('language-phrases', LanguagePhraseViewSet)

urlpatterns = router.urls + [
    path('translate/', auto_translate_phrase),
    path('rituals/', ritual_practices),
]