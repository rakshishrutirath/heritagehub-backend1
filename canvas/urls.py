from django.urls import path
from .views import save_canvas_artwork, canvas_artworks


urlpatterns = [
    path('save/', save_canvas_artwork, name='save_canvas_artwork'),
    path('artworks/', canvas_artworks, name='canvas_artworks'),
]