from django.urls import path
from . import views

app_name = 'consultations'

urlpatterns = [
    path('', views.ConsultationListView.as_view(), name='list'),
]
