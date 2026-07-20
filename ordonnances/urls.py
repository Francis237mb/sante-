from django.urls import path
from . import views

app_name = 'ordonnances'

urlpatterns = [
    path('', views.OrdonnanceListView.as_view(), name='list'),
]
