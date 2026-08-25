from django.db import models
import uuid


class CanvasArtwork(models.Model):

    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False
    )

    title = models.CharField(
        max_length=200,
        blank=True
    )

    # Original/template image used for the canvas
    template_image = models.ImageField(
        upload_to='canvas/templates/',
        blank=True,
        null=True
    )

    # Final artwork created by the user
    artwork_image = models.ImageField(
        upload_to='canvas/artworks/',
        blank=True,
        null=True
    )

    created_at = models.DateTimeField(
        auto_now_add=True
    )

    updated_at = models.DateTimeField(
        auto_now=True
    )

    def __str__(self):
        return self.title or f"Canvas Artwork - {self.id}"