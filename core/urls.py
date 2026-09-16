from django.urls import path
from . import views

app_name = 'core'

urlpatterns = [
    path('', views.HomeView.as_view(), name='home'),
    path('about/', views.AboutView.as_view(), name='about'),
    path('cgu/', views.CGUView.as_view(), name='cgu'),
    path('support/signaler/', views.SubmitReportView.as_view(), name='submit_report'),
    path('support/mes-signalements/', views.MyReportsView.as_view(), name='my_reports'),
    path('api/toggle-dark-mode/', views.toggle_dark_mode, name='toggle_dark_mode'),
]
