from django.urls import path
from . import views

app_name = 'patients'

urlpatterns = [
    path('dashboard/', views.DashboardView.as_view(), name='dashboard'),
    path('suivi/', views.PatientSuiviView.as_view(), name='suivi'),
    path('settings/', views.PatientSettingsView.as_view(), name='settings'),
    path('medecin/<int:pk>/', views.DoctorDetailView.as_view(), name='doctor_detail'),
    path('medecin/<int:pk>/subscribe/', views.DoctorSubscribeToggleView.as_view(), name='doctor_subscribe_toggle'),
]
