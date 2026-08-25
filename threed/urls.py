from django.urls import path
from .views import generate_3d_from_image, check_3d_status

urlpatterns = [
    path('generate/', generate_3d_from_image),
    path('status/<uuid:generation_id>/', check_3d_status),
]