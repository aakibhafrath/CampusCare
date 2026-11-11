"""
CampusCare URL Configuration
"""
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.views.generic import RedirectView

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', RedirectView.as_view(url='/accounts/login/', permanent=False), name='home'),
    path('accounts/', include('accounts.urls', namespace='accounts')),
    path('complaints/', include('complaints.urls', namespace='complaints')),
    path('notifications/', include('notifications.urls', namespace='notifications')),
    path('reports/', include('reports.urls', namespace='reports')),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
