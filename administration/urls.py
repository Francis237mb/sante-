from django.urls import path
from . import views

app_name = 'administration'

urlpatterns = [
    # Tableau de bord principal
    path('', views.DashboardView.as_view(), name='dashboard'),

    # Utilisateurs
    path('users/', views.UserListView.as_view(), name='users_list'),
    path('users/export/', views.UserExportCSVView.as_view(), name='users_export'),
    path('users/<int:pk>/', views.UserDetailView.as_view(), name='user_detail'),
    path('users/<int:pk>/toggle-status/', views.UserToggleStatusView.as_view(), name='user_toggle_status'),
    path('users/<int:pk>/reset-password/', views.UserResetPasswordView.as_view(), name='user_reset_password'),
    path('users/<int:pk>/deactivate/', views.UserDeactivateView.as_view(), name='user_deactivate'),
    path('users/<int:pk>/archive/', views.UserArchiveView.as_view(), name='user_archive'),

    # Demandes Médecins
    path('requests/doctors/', views.DoctorRequestsView.as_view(), name='doctor_requests'),
    path('requests/doctors/<int:pk>/approve/', views.DoctorApproveView.as_view(), name='doctor_approve'),
    path('requests/doctors/<int:pk>/reject/', views.DoctorRejectView.as_view(), name='doctor_reject'),

    # Demandes Pharmacies
    path('requests/pharmacies/', views.PharmacyRequestsView.as_view(), name='pharmacy_requests'),
    path('requests/pharmacies/<int:pk>/approve/', views.PharmacyApproveView.as_view(), name='pharmacy_approve'),
    path('requests/pharmacies/<int:pk>/reject/', views.PharmacyRejectView.as_view(), name='pharmacy_reject'),

    # Statistiques et Rapports
    path('analytics/', views.AnalyticsView.as_view(), name='analytics'),

    # Apparence
    path('appearance/', views.AppearanceView.as_view(), name='appearance'),

    # Signalements et Litiges
    path('reports/', views.ReportListView.as_view(), name='report_list'),
    path('reports/<int:pk>/', views.ReportDetailView.as_view(), name='report_detail'),

    # Contenu statique
    path('static-pages/', views.StaticPageListView.as_view(), name='static_pages'),
    path('static-pages/<int:pk>/edit/', views.StaticPageEditView.as_view(), name='static_page_edit'),

    # Logs
    path('logs/', views.ActivityLogView.as_view(), name='activity_logs'),
    
    # Paramètres Administrateur
    path('settings/', views.AdminSettingsView.as_view(), name='settings'),
    path('settings/password/', views.AdminPasswordChangeView.as_view(), name='password_change'),
    
    # Gestion des administrateurs
    path('admins/', views.AdminManagementView.as_view(), name='admins_list'),
    path('admins/<int:pk>/assign-group/', views.AdminAssignGroupView.as_view(), name='admin_assign_group'),
]
