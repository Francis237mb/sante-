from django.urls import path
from . import views

app_name = 'accounts'

urlpatterns = [
    path('login/', views.LoginPatientView.as_view(), name='login'),
    path('login/patient/', views.LoginPatientView.as_view(), name='login_patient'),
    path('login/medecin/', views.LoginMedecinView.as_view(), name='login_medecin'),
    path('login/pharmacie/', views.LoginPharmacieView.as_view(), name='login_pharmacie'),
    path('logout/', views.LogoutView.as_view(), name='logout'),
    path('register/', views.RegisterView.as_view(), name='register'),
]
