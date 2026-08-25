from rest_framework import viewsets
from .models import Product, ProductCategory
from .serializers import (
    ProductSerializer,
    ProductCategorySerializer
)


class ProductCategoryViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = ProductCategory.objects.all()
    serializer_class = ProductCategorySerializer


class ProductViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = ProductSerializer

    def get_queryset(self):
        return Product.objects.filter(
            is_active=True
        ).order_by('display_order')[:10]