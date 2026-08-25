from django.db import models
import uuid


class ProductCategory(models.Model):
    name = models.CharField(max_length=100)

    def __str__(self):
        return self.name


class Product(models.Model):
    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False
    )

    name = models.CharField(max_length=200)

    description = models.TextField()

    price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        blank=True,
        null=True
    )

    category = models.ForeignKey(
        ProductCategory,
        on_delete=models.SET_NULL,
        null=True,
        blank=True
    )

    image = models.ImageField(
        upload_to='shopping_products/',
        blank=True,
        null=True
    )

    # Real external website where user can buy the product
    buy_url = models.URLField(
        max_length=1000
    )

    # Controls the order of the 10 products
    display_order = models.PositiveIntegerField(default=0)

    # Lets you hide a product without deleting it
    is_active = models.BooleanField(default=True)

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['display_order']
        indexes = [
            models.Index(fields=['name']),
        ]

    def __str__(self):
        return self.name