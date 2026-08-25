from rest_framework import viewsets, filters
from rest_framework.permissions import IsAuthenticatedOrReadOnly
from .models import HeritageRecord, Category, Language, Location
from .serializers import HeritageRecordSerializer, CategorySerializer, LanguageSerializer, LocationSerializer

class CategoryViewSet(viewsets.ModelViewSet):
    queryset = Category.objects.all()
    serializer_class = CategorySerializer

class LanguageViewSet(viewsets.ModelViewSet):
    queryset = Language.objects.all()
    serializer_class = LanguageSerializer

class LocationViewSet(viewsets.ModelViewSet):
    queryset = Location.objects.all()
    serializer_class = LocationSerializer

class HeritageRecordViewSet(viewsets.ModelViewSet):
    queryset = HeritageRecord.objects.all().order_by('-created_at')
    serializer_class = HeritageRecordSerializer
    permission_classes = [IsAuthenticatedOrReadOnly]
    filter_backends = [filters.SearchFilter]
    search_fields = ['title', 'description', 'category__name', 'language__name', 'location__district']

    def perform_create(self, serializer):
        serializer.save(contributor=self.request.user)
