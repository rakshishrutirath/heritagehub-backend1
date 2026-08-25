from django.urls import path
from .views import generate_ai_assistance, heritage_ai_chat

urlpatterns = [
    path('assist/<uuid:record_id>/', generate_ai_assistance),

    # Floating HeritageHub AI chatbot
    path('chat/', heritage_ai_chat, name='heritage_ai_chat'),
]