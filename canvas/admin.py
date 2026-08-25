from django.contrib import admin
from .models import CanvasArtwork


@admin.register(CanvasArtwork)
class CanvasArtworkAdmin(admin.ModelAdmin):
    list_display = (
        'title',
        'created_at',
        'updated_at',
    )

    search_fields = (
        'title',
    )

    ordering = (
        '-created_at',
    )