"""
URL configuration for fransick project.
"""
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('admin/', admin.site.urls),
    path('i18n/', include('django.conf.urls.i18n')),  # Built-in view to set language
    path('', include('core.urls')),
    path('accounts/', include('accounts.urls')),
    path('patients/', include('patients.urls')),
    path('medecins/', include('medecins.urls')),
    path('pharmacies/', include('pharmacies.urls')),
    path('consultations/', include('consultations.urls')),
    path('ordonnances/', include('ordonnances.urls')),
    path('ia_assistant/', include('ia_assistant.urls')),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
