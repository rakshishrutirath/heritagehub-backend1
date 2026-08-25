from django.urls import path
from .views import impact_stats

urlpatterns = [
    path('stats/', impact_stats),
]
