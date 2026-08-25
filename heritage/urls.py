from rest_framework.routers import DefaultRouter
from .views import HeritageRecordViewSet, CategoryViewSet, LanguageViewSet, LocationViewSet

router = DefaultRouter()
router.register('records', HeritageRecordViewSet)
router.register('categories', CategoryViewSet)
router.register('languages', LanguageViewSet)
router.register('locations', LocationViewSet)

urlpatterns = router.urls