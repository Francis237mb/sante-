from django.urls import path
from . import views

app_name = 'patients'

urlpatterns = [
    path('dashboard/', views.DashboardView.as_view(), name='dashboard'),
    path('suivi/', views.PatientSuiviView.as_view(), name='suivi'),
    path('settings/', views.PatientSettingsView.as_view(), name='settings'),
    path('pharmacies/', views.PharmacyListView.as_view(), name='pharmacies'),
    path('videos/', views.PatientVideosFeedView.as_view(), name='videos_feed'),
    path('video/<int:pk>/like/', views.ToggleVideoLikeView.as_view(), name='toggle_video_like'),
    path('medecin/<int:pk>/', views.DoctorDetailView.as_view(), name='doctor_detail'),
    path('medecin/<int:pk>/book/', views.BookAppointmentView.as_view(), name='book_appointment'),
    path('medecin/<int:pk>/subscribe/', views.DoctorSubscribeToggleView.as_view(), name='doctor_subscribe_toggle'),
    path('api/medecins/live/', views.api_live_medecins, name='api_live_medecins'),
]
