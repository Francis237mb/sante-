from django.urls import path
from . import views

app_name = 'medecins'

urlpatterns = [
    path('dashboard/', views.DashboardView.as_view(), name='dashboard'),
]
