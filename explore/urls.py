from rest_framework.routers import DefaultRouter
from .views import ExplorePlaceViewSet, ExploreEraViewSet

router = DefaultRouter()

router.register('places', ExplorePlaceViewSet, basename='explore-place')
router.register('eras', ExploreEraViewSet, basename='explore-era')

urlpatterns = router.urls