from django.urls import path
from . import views

app_name = 'paiements'

urlpatterns = [
    # Initier un paiement (GET: formulaire, POST: soumission)
    path('payer/<int:doctor_id>/<str:payment_type>/', views.InitiatePaymentView.as_view(), name='initiate'),

    # Page d'attente et polling statut
    path('statut/<uuid:paiement_ref>/', views.PaymentStatusView.as_view(), name='status'),
    path('api/statut/<uuid:paiement_ref>/', views.CheckPaymentStatusAjaxView.as_view(), name='check_status_ajax'),

    # Reçu
    path('recu/<uuid:paiement_ref>/', views.ViewReceiptView.as_view(), name='receipt'),
    path('recu/<uuid:paiement_ref>/telecharger/', views.DownloadReceiptView.as_view(), name='download_receipt'),

    # Historique
    path('historique/', views.PaymentHistoryView.as_view(), name='history'),

    # Webhook CamPay (notification asynchrone)
    path('webhook/campay/', views.CamPayWebhookView.as_view(), name='campay_webhook'),
]
