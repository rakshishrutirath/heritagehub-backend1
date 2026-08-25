from django.db import models
import uuid


class ThreeDGeneration(models.Model):

    STATUS_CHOICES = (
        ('pending', 'Pending'),
        ('processing', 'Processing'),
        ('succeeded', 'Succeeded'),
        ('failed', 'Failed'),
    )

    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False
    )

    # Image uploaded by the user
    image = models.ImageField(
        upload_to='threed/input_images/'
    )

    # Meshy task ID returned after generation starts
    meshy_task_id = models.CharField(
        max_length=200,
        blank=True,
        null=True
    )

    # Current generation status
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='pending'
    )

    # Final generated GLB model URL from Meshy
    model_url = models.URLField(
        max_length=1000,
        blank=True,
        null=True
    )

    # Store error message if Meshy generation fails
    error_message = models.TextField(
        blank=True,
        null=True
    )
    
    model_file = models.FileField(
      upload_to="3d/models/",
      null=True,
      blank=True
    )
        
    created_at = models.DateTimeField(
        auto_now_add=True
    )

    updated_at = models.DateTimeField(
        auto_now=True
    )
    
    def __str__(self):
        return f"3D Generation - {self.id} - {self.status}"
    
