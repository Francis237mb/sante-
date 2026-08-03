from django.urls import path
from . import views

app_name = 'ordonnances'

urlpatterns = [
    path('', views.OrdonnanceListView.as_view(), name='list'),
    path('creer/<int:rdv_id>/', views.CreateOrdonnanceView.as_view(), name='create_for_rdv'),
    path('creer/', views.CreateOrdonnanceView.as_view(), name='create'),
    path('<int:pk>/', views.OrdonnanceDetailView.as_view(), name='detail'),
    path('<int:pk>/envoyer/', views.SendOrdonnanceToPatientView.as_view(), name='send_to_patient'),
]
