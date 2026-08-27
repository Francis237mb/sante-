from django.urls import path
from . import views

app_name = 'consultations'

urlpatterns = [
    path('', views.ConsultationListView.as_view(), name='list'),
    path('rdv/<int:pk>/join/', views.JoinWaitingRoomView.as_view(), name='join_waiting_room'),
    path('rdv/<int:pk>/waiting/', views.PatientWaitingRoomView.as_view(), name='patient_waiting_room'),
    path('rdv/<int:pk>/status/', views.CheckRdvStatusView.as_view(), name='check_rdv_status'),
    path('rdv/waiting-list/', views.DoctorWaitingRoomListView.as_view(), name='doctor_waiting_list'),
    path('rdv/<int:pk>/start/', views.StartConsultationView.as_view(), name='start_consultation'),
    path('rdv/<int:pk>/room/', views.ConsultationRoomView.as_view(), name='room'),
    path('rdv/<int:pk>/end/', views.EndConsultationView.as_view(), name='end_consultation'),
    path('rdv/<int:pk>/accept/', views.AcceptAppointmentView.as_view(), name='accept_appointment'),
    path('rdv/<int:pk>/reject/', views.RejectAppointmentView.as_view(), name='reject_appointment'),
    path('rdv/direct/', views.CreateDirectConsultationView.as_view(), name='create_direct_consultation'),
]
