from django.urls import path
from . import views

app_name = 'medecins'

urlpatterns = [
    path('dashboard/', views.DashboardView.as_view(), name='dashboard'),
    path('patients/', views.DoctorPatientsListView.as_view(), name='patients'),
    path('settings/', views.DoctorSettingsView.as_view(), name='settings'),
    path('video/<int:pk>/comment/', views.AddVideoCommentView.as_view(), name='add_video_comment'),
    path('video/<int:pk>/delete/', views.DeleteVideoView.as_view(), name='delete_video'),
]
