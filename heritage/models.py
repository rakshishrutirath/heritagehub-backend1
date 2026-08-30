from django.db import models
from django.conf import settings
from django.core.files.storage import FileSystemStorage
import uuid

from django.db.models.signals import post_save
from django.dispatch import receiver


# ============================================================
# QR CODE LOCAL STORAGE
# ============================================================

qr_storage = FileSystemStorage(
    location="/home/rakshi/heritagehub-backend1/media/qr_codes",
    base_url="/media/qr_codes/"
)


# ============================================================
# CATEGORY
# ============================================================

class Category(models.Model):

    name = models.CharField(
        max_length=100
    )

    def __str__(self):
        return self.name


# ============================================================
# LANGUAGE
# ============================================================

class Language(models.Model):

    name = models.CharField(
        max_length=100
    )

    def __str__(self):
        return self.name


# ============================================================
# LOCATION
# ============================================================

class Location(models.Model):

    village_or_area = models.CharField(
        max_length=150
    )

    district = models.CharField(
        max_length=100
    )

    state = models.CharField(
        max_length=100,
        default="Odisha"
    )

    def __str__(self):
        return f"{self.village_or_area}, {self.district}"


# ============================================================
# HERITAGE RECORD
# ============================================================

class HeritageRecord(models.Model):

    STATUS_CHOICES = (
        ("pending", "Pending Review"),
        ("approved", "Approved"),
        ("rejected", "Needs Correction"),
    )

    # --------------------------------------------------------
    # Basic information
    # --------------------------------------------------------

    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False
    )

    title = models.CharField(
        max_length=200
    )

    description = models.TextField()

    # --------------------------------------------------------
    # Classification
    # --------------------------------------------------------

    category = models.ForeignKey(
        Category,
        on_delete=models.SET_NULL,
        null=True
    )

    language = models.ForeignKey(
        Language,
        on_delete=models.SET_NULL,
        null=True
    )

    location = models.ForeignKey(
        Location,
        on_delete=models.SET_NULL,
        null=True,
        blank=True
    )

    # --------------------------------------------------------
    # Contributor
    # --------------------------------------------------------

    contributor = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="submissions"
    )

    # --------------------------------------------------------
    # Media
    # --------------------------------------------------------

    image = models.ImageField(
        upload_to="heritage_images/",
        blank=True,
        null=True
    )

    audio = models.FileField(
        upload_to="heritage_audio/",
        blank=True,
        null=True
    )

    # --------------------------------------------------------
    # AI generated information
    # --------------------------------------------------------

    ai_summary = models.TextField(
        blank=True,
        null=True
    )

    ai_tags = models.CharField(
        max_length=300,
        blank=True,
        null=True
    )

    ai_translation = models.TextField(
        blank=True,
        null=True
    )

    # --------------------------------------------------------
    # User consent
    # --------------------------------------------------------

    consent_given = models.BooleanField(
        default=False
    )

    # --------------------------------------------------------
    # Verification
    # --------------------------------------------------------

    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default="pending"
    )

    verified_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="verified_records"
    )

    # --------------------------------------------------------
    # QR CODE
    # --------------------------------------------------------
    # QR code is stored locally on PythonAnywhere.
    # This avoids Cloudinary being used for QR generation.

    qr_code = models.ImageField(
        storage=qr_storage,
        upload_to="",
        blank=True,
        null=True
    )

    # --------------------------------------------------------
    # Timestamp
    # --------------------------------------------------------

    created_at = models.DateTimeField(
        auto_now_add=True
    )

    # --------------------------------------------------------
    # Database indexes
    # --------------------------------------------------------

    class Meta:

        indexes = [
            models.Index(
                fields=["status"]
            ),
            models.Index(
                fields=["title"]
            ),
        ]

    def __str__(self):
        return self.title


# ============================================================
# AUTOMATIC QR CODE GENERATION
# ============================================================

@receiver(
    post_save,
    sender=HeritageRecord
)
def create_qr_code(
    sender,
    instance,
    created,
    **kwargs
):

    # --------------------------------------------------------
    # Generate QR only after approval
    # --------------------------------------------------------

    if (
        instance.status == "approved"
        and not instance.qr_code
    ):

        from .utils import generate_qr_for_record

        try:

            # Generate QR image
            generate_qr_for_record(instance)

            # Save QR code only
            if instance.qr_code:

                instance.save(
                    update_fields=["qr_code"]
                )

        except Exception as e:

            # QR generation should NEVER
            # break the approval process.

            print(
                f"QR generation failed for "
                f"{instance.id}: {e}"
            )