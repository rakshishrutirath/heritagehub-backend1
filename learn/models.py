from django.db import models


class Song(models.Model):
    GENRE_CHOICES = (
        ('sambalpuri', 'Sambalpuri'),
        ('koraputia', 'Koraputia'),
        ('bhajan', 'Odia Bhajan'),
        ('santali', 'Santali'),
    )

    title = models.CharField(max_length=200)

    genre = models.CharField(
        max_length=20,
        choices=GENRE_CHOICES
    )

    artist = models.CharField(
        max_length=200,
        blank=True
    )

    region = models.CharField(
        max_length=150,
        blank=True
    )

    image = models.ImageField(
        upload_to='learn_songs_images/',
        blank=True,
        null=True
    )

    youtube_url = models.URLField(
        blank=True
    )

    # Local/Django file field
    # Keep this for existing uploaded files.
    audio = models.FileField(
        upload_to='learn_songs/',
        blank=True,
        null=True
    )

    # Permanent Cloudinary RAW audio URL
    # This is the URL your frontend should use for playing songs.
    cloudinary_audio_url = models.URLField(
        blank=True,
        null=True
    )

    lyrics = models.TextField(
        blank=True
    )

    cultural_context = models.TextField(
        blank=True
    )

    created_at = models.DateTimeField(
        auto_now_add=True
    )

    class Meta:
        indexes = [
            models.Index(fields=['title']),
            models.Index(fields=['genre']),
        ]

    def __str__(self):
        return self.title


class DancePose(models.Model):
    DANCE_CHOICES = (
        ('odissi', 'Odissi'),
        ('dhemsa', 'Dhemsa'),
        ('sambalpuri', 'Sambalpuri'),
    )

    dance_name = models.CharField(
        max_length=20,
        choices=DANCE_CHOICES,
        default='odissi'
    )

    pose_name = models.CharField(
        max_length=150
    )

    image = models.ImageField(
        upload_to='learn_dance/',
        blank=True,
        null=True
    )

    explanation = models.TextField(
        blank=True
    )

    tutorial_link = models.URLField(
        blank=True
    )

    order = models.PositiveIntegerField(
        default=0
    )

    class Meta:
        ordering = ['order']

        indexes = [
            models.Index(fields=['dance_name']),
        ]

    def __str__(self):
        return f"{self.dance_name} - {self.pose_name}"


class LanguagePhrase(models.Model):
    CATEGORY_CHOICES = (
        ('greetings', 'Greetings'),
        ('everyday', 'Everyday Words'),
        ('family', 'Family'),
        ('food', 'Food'),
        ('travel', 'Travel'),
        ('culture', 'Culture'),
        ('numbers', 'Numbers'),
        ('sentences', 'Common Sentences'),
    )

    category = models.CharField(
        max_length=20,
        choices=CATEGORY_CHOICES
    )

    english_phrase = models.CharField(
        max_length=300
    )

    odia_translation = models.CharField(
        max_length=300
    )

    audio = models.FileField(
        upload_to='learn_language/',
        blank=True,
        null=True
    )

    class Meta:
        indexes = [
            models.Index(fields=['category']),
        ]

    def __str__(self):
        return f"{self.english_phrase} → {self.odia_translation}"


class RitualPractice(models.Model):
    title = models.CharField(
        max_length=200
    )

    region = models.CharField(
        max_length=150,
        blank=True
    )

    description = models.TextField()

    cultural_significance = models.TextField(
        blank=True
    )

    practices = models.TextField(
        blank=True
    )

    image = models.ImageField(
        upload_to='learn_rituals/',
        blank=True,
        null=True
    )

    created_at = models.DateTimeField(
        auto_now_add=True
    )

    class Meta:
        ordering = ['title']

        indexes = [
            models.Index(fields=['title']),
            models.Index(fields=['region']),
        ]

    def __str__(self):
        return self.title