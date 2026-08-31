from django.db import models
from django.core.files.storage import FileSystemStorage
import uuid


# ============================================================
# LOCAL STORAGE
# ============================================================
# These 3D files should NOT go through Cloudinary.
# They will be stored in Django's local MEDIA_ROOT.
# ============================================================

local_storage = FileSystemStorage()


class ThreeDGeneration(models.Model):

    STATUS_CHOICES = (
        ('pending', 'Pending'),
        ('processing', 'Processing'),
        ('succeeded', 'Succeeded'),
        ('failed', 'Failed'),
    )

    # ========================================================
    # PRIMARY KEY
    # ========================================================

    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False
    )

    # ========================================================
    # INPUT IMAGE
    # ========================================================
    # Stored locally instead of Cloudinary.
    # ========================================================

    image = models.ImageField(
        storage=local_storage,
        upload_to='threed/input_images/'
    )

    # ========================================================
    # MESHY TASK ID
    # ========================================================

    meshy_task_id = models.CharField(
        max_length=200,
        blank=True,
        null=True
    )

    # ========================================================
    # GENERATION STATUS
    # ========================================================

    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='pending'
    )

    # ========================================================
    # ORIGINAL MESHY MODEL URL
    # ========================================================
    # We keep this for reference.
    # The frontend should use model_file instead.
    # ========================================================

    model_url = models.URLField(
        max_length=1000,
        blank=True,
        null=True
    )

    # ========================================================
    # ERROR MESSAGE
    # ========================================================

    error_message = models.TextField(
        blank=True,
        null=True
    )

    # ========================================================
    # LOCALLY STORED GLB MODEL
    # ========================================================
    # IMPORTANT:
    # This is also stored locally.
    # It prevents the frontend from directly accessing
    # assets.meshy.ai and avoids the Meshy CORS problem.
    # ========================================================

    model_file = models.FileField(
        storage=local_storage,
        upload_to='3d/models/',
        null=True,
        blank=True
    )

    # ========================================================
    # TIMESTAMPS
    # ========================================================

    created_at = models.DateTimeField(
        auto_now_add=True
    )

    updated_at = models.DateTimeField(
        auto_now=True
    )

    # ========================================================
    # STRING REPRESENTATION
    # ========================================================

    def __str__(self):
        return (
            f"3D Generation - "
            f"{self.id} - "
            f"{self.status}"
        )