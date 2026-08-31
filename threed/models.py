from django.db import models
from django.core.files.storage import FileSystemStorage
import uuid


class ThreeDGeneration(models.Model):

    STATUS_CHOICES = (
        ('pending', 'Pending'),
        ('processing', 'Processing'),
        ('succeeded', 'Succeeded'),
        ('failed', 'Failed'),
    )

    # ============================================================
    # PRIMARY KEY
    # ============================================================

    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False
    )

    # ============================================================
    # INPUT IMAGE
    # ============================================================
    # IMPORTANT:
    # Use local filesystem storage for the 3D input image.
    # This prevents Cloudinary from being used for this field.
    # ============================================================

    image = models.ImageField(
        storage=FileSystemStorage(),
        upload_to='threed/input_images/'
    )

    # ============================================================
    # MESHY TASK ID
    # ============================================================

    meshy_task_id = models.CharField(
        max_length=200,
        blank=True,
        null=True
    )

    # ============================================================
    # GENERATION STATUS
    # ============================================================

    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='pending'
    )

    # ============================================================
    # FINAL MESHY MODEL URL
    # ============================================================

    model_url = models.URLField(
        max_length=1000,
        blank=True,
        null=True
    )

    # ============================================================
    # ERROR MESSAGE
    # ============================================================

    error_message = models.TextField(
        blank=True,
        null=True
    )

    # ============================================================
    # OPTIONAL LOCAL GLB FILE
    # ============================================================

    model_file = models.FileField(
        upload_to='3d/models/',
        null=True,
        blank=True
    )

    # ============================================================
    # TIMESTAMPS
    # ============================================================

    created_at = models.DateTimeField(
        auto_now_add=True
    )

    updated_at = models.DateTimeField(
        auto_now=True
    )

    # ============================================================
    # STRING REPRESENTATION
    # ============================================================

    def __str__(self):
        return (
            f"3D Generation - "
            f"{self.id} - "
            f"{self.status}"
        )