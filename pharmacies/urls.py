from django.urls import path
from . import views

app_name = 'pharmacies'

urlpatterns = [
    path('', views.PharmacyListView.as_view(), name='list'),
]
