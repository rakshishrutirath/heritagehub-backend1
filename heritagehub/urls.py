from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/heritage/', include('heritage.urls')),
    path('api/accounts/', include('accounts.urls')),
    path('api/community/', include('community.urls')),
    path('api/ai/', include('ai_assistant.urls')),
    path('api/dashboard/', include('dashboard.urls')),
    path('api/shopping/', include('shopping.urls')),
    path('api/learn/', include('learn.urls')),
    path('api/explore/', include('explore.urls')),
    path('api/3d/', include('threed.urls')),
    path('api/canvas/', include('canvas.urls')),
]

if settings.DEBUG:
    from django.conf import settings as s
    urlpatterns += static(s.MEDIA_URL, document_root=s.BASE_DIR / 'media')
