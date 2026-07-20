from django.urls import path
from . import views

app_name = 'patients'

urlpatterns = [
    path('dashboard/', views.DashboardView.as_view(), name='dashboard'),
    path('suivi/', views.PatientSuiviView.as_view(), name='suivi'),
    path('settings/', views.PatientSettingsView.as_view(), name='settings'),
]
