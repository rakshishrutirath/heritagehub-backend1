from django.contrib import admin
from .models import Song, DancePose, LanguagePhrase, RitualPractice

admin.site.register(Song)
admin.site.register(DancePose)
admin.site.register(LanguagePhrase)
admin.site.register(RitualPractice)
