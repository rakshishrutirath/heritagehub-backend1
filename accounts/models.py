from django.contrib.auth.models import AbstractUser
from django.db import models

class User(AbstractUser):
    ROLE_CHOICES = (
        ('contributor', 'Contributor'),
        ('verifier', 'Verifier'),
        ('admin', 'Admin'),
    )
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='contributor')
    community = models.CharField(max_length=150, blank=True, null=True)
    bio = models.TextField(blank=True, null=True)