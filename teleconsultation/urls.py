from django.urls import path
from . import views

app_name = 'teleconsultation'

urlpatterns = [
    path('rejoindre/<int:rdv_id>/', views.rejoindre_appel, name='rejoindre_appel'),
    path('terminer/<int:appel_id>/', views.terminer_appel, name='terminer_appel'),
]
