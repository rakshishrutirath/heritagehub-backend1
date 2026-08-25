from django.urls import path
from .views import review_record

urlpatterns = [
    path('review/<uuid:record_id>/', review_record),
]
