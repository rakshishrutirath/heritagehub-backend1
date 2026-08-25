from django.db import models
import uuid


class ExplorePlace(models.Model):
    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False
    )

    name = models.CharField(max_length=200)

    district = models.CharField(
        max_length=100,
        blank=True
    )

    short_description = models.TextField()

    main_image = models.ImageField(
        upload_to='explore/main/',
        blank=True,
        null=True
    )

    culture_title = models.CharField(
        max_length=200,
        blank=True
    )

    culture_description = models.TextField(
        blank=True
    )

    culture_image = models.ImageField(
        upload_to='explore/culture/',
        blank=True,
        null=True
    )

    food_title = models.CharField(
        max_length=200,
        blank=True
    )

    food_description = models.TextField(
        blank=True
    )

    food_image = models.ImageField(
        upload_to='explore/food/',
        blank=True,
        null=True
    )

    story_audio = models.FileField(
        upload_to='explore/audio/',
        blank=True,
        null=True
    )

    display_order = models.PositiveIntegerField(
        default=0
    )

    is_active = models.BooleanField(
        default=True
    )

    created_at = models.DateTimeField(
        auto_now_add=True
    )

    class Meta:
        ordering = ['display_order']

    def __str__(self):
        return self.name


class ExploreEra(models.Model):
    place = models.ForeignKey(
        ExplorePlace,
        on_delete=models.CASCADE,
        related_name='eras'
    )

    era_name = models.CharField(
        max_length=100
    )

    year = models.IntegerField()

    image = models.ImageField(
        upload_to='explore/eras/',
        blank=True,
        null=True
    )

    description = models.TextField()

    order = models.PositiveIntegerField(
        default=0
    )

    class Meta:
        ordering = ['order']

    def __str__(self):
        return f"{self.place.name} - {self.era_name}"