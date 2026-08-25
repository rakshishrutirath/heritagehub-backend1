from rest_framework import viewsets
from .models import ExplorePlace, ExploreEra
from .serializers import ExplorePlaceSerializer, ExploreEraSerializer


class ExplorePlaceViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = ExplorePlaceSerializer

    def get_queryset(self):
        return ExplorePlace.objects.filter(
            is_active=True
        ).order_by('display_order')


class ExploreEraViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = ExploreEra.objects.all().order_by('order')
    serializer_class = ExploreEraSerializer

    def get_queryset(self):
        queryset = super().get_queryset()

        place_id = self.request.query_params.get('place')

        if place_id:
            queryset = queryset.filter(place_id=place_id)

        return queryset