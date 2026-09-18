import json
import logging
from decimal import Decimal
from django.conf import settings
from django.contrib import messages
from django.contrib.auth import get_user_model
from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import JsonResponse, HttpResponse
from django.shortcuts import render, redirect, get_object_or_404
from django.utils import timezone
from django.views import View
from django.views.generic import TemplateView
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator

from consultations.models import RendezVous
from medecins.models import DoctorProfile
from .models import Paiement
from .services import campay_service
from .services.receipt_service import generate_receipt_pdf

logger = logging.getLogger(__name__)
User = get_user_model()

DEPOSIT_PERCENT = getattr(settings, 'CAMPAY_DEPOSIT_PERCENT', 20)


# ─────────────────────────────────────────────────────────────────────────────
# INITIATION DU PAIEMENT
# ─────────────────────────────────────────────────────────────────────────────

class InitiatePaymentView(LoginRequiredMixin, View):
    """
    Affiche le formulaire de paiement et initie la transaction CamPay.
    Accessible via GET (formulaire) et POST (soumission).

    URL params attendus:
    - doctor_id: ID du médecin
    - payment_type: 'rdv' (acompte 20%) ou 'direct' (paiement total)
    """
    template_name = 'paiements/initiate_payment.html'

    def _get_doctor_fee(self, doctor):
        """Récupère le tarif du médecin (-1 si non défini)."""
        profile = getattr(doctor, 'doctor_profile', None)
        if profile and profile.consultation_fee is not None:
            return Decimal(str(profile.consultation_fee))
        return Decimal('-1')

    def get(self, request, doctor_id, payment_type, *args, **kwargs):
        doctor = get_object_or_404(User, pk=doctor_id, role='medecin')
        fee = self._get_doctor_fee(doctor)

        if fee < 0:
            messages.error(request, "Ce médecin n'a pas encore renseigné son tarif de consultation.")
            return redirect('patients:doctor_detail', pk=doctor_id)

        if fee == 0:
            messages.info(request, "La consultation est gratuite, aucun paiement n'est requis.")
            return redirect('patients:doctor_detail', pk=doctor_id)

        if payment_type == 'rdv':
            amount = (fee * DEPOSIT_PERCENT / 100).quantize(Decimal('1'))
            label = f"Acompte RDV (20%) — Dr. {doctor.get_full_name() or doctor.username}"
        else:  # direct
            amount = fee
            label = f"Consultation Directe — Dr. {doctor.get_full_name() or doctor.username}"

        context = {
            'doctor': doctor,
            'doctor_profile': getattr(doctor, 'doctor_profile', None),
            'payment_type': payment_type,
            'fee': fee,
            'amount': amount,
            'deposit_percent': DEPOSIT_PERCENT,
            'label': label,
            'phone_prefill': getattr(request.user, 'phone_number', ''),
            # Récupérer les params RDV depuis GET
            'rdv_date': request.GET.get('date', ''),
            'rdv_time': request.GET.get('time_slot', '10:00'),
            'rdv_reason': request.GET.get('reason', 'Consultation médicale'),
            'rdv_consultation_type': request.GET.get('consultation_type', 'video'),
            # Préfixes opérateurs pour détection JS
            'mtn_prefixes_json': json.dumps(campay_service.MTN_PREFIXES),
            'orange_prefixes_json': json.dumps(campay_service.ORANGE_PREFIXES),
        }
        return render(request, self.template_name, context)

    def post(self, request, doctor_id, payment_type, *args, **kwargs):
        doctor = get_object_or_404(User, pk=doctor_id, role='medecin')
        fee = self._get_doctor_fee(doctor)
        phone = request.POST.get('phone_number', '').strip()

        if not phone:
            messages.error(request, "Veuillez entrer votre numéro de téléphone Mobile Money.")
            return redirect('paiements:initiate', doctor_id=doctor_id, payment_type=payment_type)

        if fee < 0:
            messages.error(request, "Tarif médecin non configuré.")
            return redirect('patients:doctor_detail', pk=doctor_id)

        if fee == 0:
            messages.info(request, "La consultation est gratuite, aucun paiement n'est requis.")
            return redirect('patients:doctor_detail', pk=doctor_id)

        if payment_type == 'rdv':
            amount = int((fee * DEPOSIT_PERCENT / 100).quantize(Decimal('1')))
            ptype = Paiement.TYPE_ACOMPTE
            description = f"Acompte 20% RDV — Dr. {doctor.get_full_name() or doctor.username} — Fransick Santé"
        else:
            amount = int(fee)
            ptype = Paiement.TYPE_TOTAL
            description = f"Consultation Directe — Dr. {doctor.get_full_name() or doctor.username} — Fransick Santé"

        # Créer l'enregistrement paiement en attente (avant l'appel CamPay)
        paiement = Paiement.objects.create(
            patient=request.user,
            medecin=doctor,
            montant_total_consultation=fee,
            montant_paye=amount,
            pourcentage_acompte=DEPOSIT_PERCENT if payment_type == 'rdv' else 100,
            payment_type=ptype,
            phone_number=phone,
            status=Paiement.STATUS_PENDING,
        )

        # Sauvegarder les données du RDV en session (si rdv)
        if payment_type == 'rdv':
            rdv_data = {
                'doctor_id': doctor_id,
                'consultation_type': request.POST.get('consultation_type', 'video'),
                'date': request.POST.get('date', ''),
                'time_slot': request.POST.get('time_slot', '10:00'),
                'reason': request.POST.get('reason', 'Consultation médicale'),
                'notes': request.POST.get('notes', ''),
            }
            request.session[f'rdv_data_{paiement.reference}'] = rdv_data

        if payment_type == 'direct':
            direct_data = {
                'doctor_id': doctor_id,
                'consultation_type': request.POST.get('consultation_type', 'video'),
            }
            request.session[f'direct_data_{paiement.reference}'] = direct_data

        # ── Appel CamPay ──────────────────────────────────────────────────────
        campay_result = campay_service.initiate_collection(
            amount=amount,
            phone=phone,
            description=description,
            external_reference=str(paiement.reference),
        )

        if campay_result['success']:
            paiement.campay_reference = campay_result['reference']
            paiement.campay_operator = campay_result.get('operator', '')
            paiement.campay_raw_response = campay_result.get('raw', {})
            paiement.save()
            return redirect('paiements:status', paiement_ref=paiement.reference)
        else:
            paiement.status = Paiement.STATUS_FAILED
            paiement.campay_raw_response = campay_result.get('raw', {})
            paiement.error_message = campay_result.get('message', '')
            paiement.save()
            messages.error(request, campay_result['message'])
            return redirect('paiements:initiate', doctor_id=doctor_id, payment_type=payment_type)


# ─────────────────────────────────────────────────────────────────────────────
# VÉRIFICATION DU STATUT (POLLING)
# ─────────────────────────────────────────────────────────────────────────────

class PaymentStatusView(LoginRequiredMixin, View):
    """Page d'attente avec polling AJAX du statut du paiement."""
    template_name = 'paiements/payment_status.html'

    def get(self, request, paiement_ref, *args, **kwargs):
        paiement = get_object_or_404(Paiement, reference=paiement_ref, patient=request.user)
        return render(request, self.template_name, {
            'paiement': paiement,
            'expiry_minutes': campay_service.PAYMENT_EXPIRY_MINUTES,
        })


class CheckPaymentStatusAjaxView(LoginRequiredMixin, View):
    """
    Endpoint AJAX appelé périodiquement pour vérifier le statut CamPay.
    Gère aussi l'expiration automatique si le paiement est resté pending > 5 min.
    """

    def get(self, request, paiement_ref, *args, **kwargs):
        paiement = get_object_or_404(Paiement, reference=paiement_ref, patient=request.user)

        # ── Déjà finalisé → répondre immédiatement ──────────────────────────
        if paiement.is_terminal:
            return JsonResponse({
                'status': paiement.status,
                'message': paiement.error_message or '',
                'redirect_url': self._get_redirect_url(request, paiement),
            })

        # ── Expiration automatique après 5 minutes ───────────────────────────
        if paiement.is_expired_pending:
            paiement.status = Paiement.STATUS_EXPIRED
            paiement.error_message = campay_service.CAMPAY_ERROR_MESSAGES['timeout']
            paiement.save()
            logger.info(f"[Paiement] {paiement.reference} expiré après 5 minutes sans confirmation.")
            return JsonResponse({
                'status': 'expired',
                'message': paiement.error_message,
                'redirect_url': None,
            })

        # ── Interroger CamPay ─────────────────────────────────────────────────
        if paiement.campay_reference:
            result = campay_service.check_transaction_status(paiement.campay_reference)
            campay_status = result.get('status', 'PENDING').upper()
            internal_status = campay_service.CAMPAY_STATUS_MAP.get(campay_status, 'pending')

            paiement.campay_operator = result.get('operator', '') or paiement.campay_operator
            paiement.campay_raw_response = result.get('raw', {})

            if internal_status == 'successful':
                paiement.status = Paiement.STATUS_SUCCESSFUL
                paiement.paid_at = timezone.now()
                paiement.save()
                self._finalize_after_payment(request, paiement)
                return JsonResponse({
                    'status': 'successful',
                    'message': '',
                    'redirect_url': self._get_redirect_url(request, paiement),
                })

            elif internal_status in ('failed', 'expired', 'cancelled'):
                paiement.status = internal_status
                paiement.error_message = result.get('message', '')
                paiement.save()
                return JsonResponse({
                    'status': internal_status,
                    'message': paiement.error_message,
                    'redirect_url': None,
                })
            else:
                paiement.save()
                return JsonResponse({'status': 'pending', 'message': ''})
        else:
            return JsonResponse({'status': 'pending', 'message': ''})

    def _finalize_after_payment(self, request, paiement):
        """Crée le RDV ou la consultation directe après confirmation du paiement."""
        import datetime
        from django.utils.crypto import get_random_string

        if paiement.payment_type == Paiement.TYPE_ACOMPTE:
            rdv_data = request.session.pop(f'rdv_data_{paiement.reference}', None)
            if rdv_data:
                try:
                    doctor = User.objects.get(pk=rdv_data['doctor_id'])
                    rdv = RendezVous.objects.create(
                        patient=paiement.patient,
                        doctor=doctor,
                        consultation_type=rdv_data.get('consultation_type', 'video'),
                        date=rdv_data.get('date', datetime.date.today()),
                        time_slot=rdv_data.get('time_slot', '10:00'),
                        reason=rdv_data.get('reason', 'Consultation médicale'),
                        notes=rdv_data.get('notes', ''),
                        status='pending',
                    )
                    paiement.rdv = rdv
                    paiement.save()
                except Exception as e:
                    logger.error(f"[Paiement] Erreur création RDV après paiement: {e}")

        elif paiement.payment_type == Paiement.TYPE_TOTAL:
            direct_data = request.session.pop(f'direct_data_{paiement.reference}', None)
            if direct_data:
                try:
                    doctor = User.objects.get(pk=direct_data['doctor_id'])
                    rdv = RendezVous.objects.create(
                        patient=paiement.patient,
                        doctor=doctor,
                        consultation_type=direct_data.get('consultation_type', 'video'),
                        date=datetime.date.today(),
                        time_slot=datetime.datetime.now().strftime("%H:%M"),
                        reason="Téléconsultation Directe",
                        status='confirmed',
                        in_waiting_room=True,
                        room_name=f"fransick_teleconsult_direct_{paiement.patient.id}_{get_random_string(8)}"
                    )
                    paiement.rdv = rdv
                    paiement.save()
                except Exception as e:
                    logger.error(f"[Paiement] Erreur création consultation directe après paiement: {e}")

    def _get_redirect_url(self, request, paiement):
        if paiement.status == Paiement.STATUS_SUCCESSFUL:
            if paiement.payment_type == Paiement.TYPE_TOTAL and paiement.rdv:
                return f'/consultations/rdv/{paiement.rdv.id}/waiting/'
            return f'/paiements/recu/{paiement.reference}/'
        return None


# ─────────────────────────────────────────────────────────────────────────────
# HISTORIQUE DES PAIEMENTS
# ─────────────────────────────────────────────────────────────────────────────

class PaymentHistoryView(LoginRequiredMixin, TemplateView):
    """Historique des paiements selon le rôle de l'utilisateur."""
    template_name = 'paiements/payment_history.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user
        role = getattr(user, 'role', '')

        if user.is_superuser or role == 'admin':
            paiements = Paiement.objects.all().select_related('patient', 'medecin', 'rdv')
            context['is_admin'] = True
        elif role == 'medecin':
            paiements = Paiement.objects.filter(medecin=user).select_related('patient', 'rdv')
            context['is_admin'] = False
        else:
            paiements = Paiement.objects.filter(patient=user).select_related('medecin', 'rdv')
            context['is_admin'] = False

        # Statistiques
        total_montant = sum(p.montant_paye for p in paiements if p.is_successful)
        context['paiements'] = paiements
        context['total_count'] = paiements.count()
        context['success_count'] = paiements.filter(status=Paiement.STATUS_SUCCESSFUL).count()
        context['pending_count'] = paiements.filter(status=Paiement.STATUS_PENDING).count()
        context['failed_count'] = paiements.filter(
            status__in=[Paiement.STATUS_FAILED, Paiement.STATUS_EXPIRED, Paiement.STATUS_CANCELLED]
        ).count()
        context['total_montant'] = total_montant
        return context


# ─────────────────────────────────────────────────────────────────────────────
# REÇU PDF
# ─────────────────────────────────────────────────────────────────────────────

class DownloadReceiptView(LoginRequiredMixin, View):
    """Génère et télécharge un reçu PDF pour un paiement réussi."""

    def get(self, request, paiement_ref, *args, **kwargs):
        paiement = get_object_or_404(Paiement, reference=paiement_ref)

        # Vérification d'accès
        user = request.user
        role = getattr(user, 'role', '')
        if not (user.is_superuser or role == 'admin' or
                paiement.patient == user or paiement.medecin == user):
            from django.core.exceptions import PermissionDenied
            raise PermissionDenied

        pdf_bytes = generate_receipt_pdf(paiement)
        ref_short = str(paiement.reference).upper()[:8]
        filename = f"Recu_Paiement_Fransick_{ref_short}.pdf"

        response = HttpResponse(pdf_bytes, content_type='application/pdf')
        response['Content-Disposition'] = f'attachment; filename="{filename}"'
        return response


class ViewReceiptView(LoginRequiredMixin, View):
    """Affiche la page de reçu (vue HTML) après un paiement réussi."""
    template_name = 'paiements/receipt.html'

    def get(self, request, paiement_ref, *args, **kwargs):
        paiement = get_object_or_404(Paiement, reference=paiement_ref)
        user = request.user
        role = getattr(user, 'role', '')
        if not (user.is_superuser or role == 'admin' or
                paiement.patient == user or paiement.medecin == user):
            from django.core.exceptions import PermissionDenied
            raise PermissionDenied
        return render(request, self.template_name, {'paiement': paiement})


# ─────────────────────────────────────────────────────────────────────────────
# WEBHOOK CAMPAY (Confirmation asynchrone sécurisée)
# ─────────────────────────────────────────────────────────────────────────────

@method_decorator(csrf_exempt, name='dispatch')
class CamPayWebhookView(View):
    """
    Endpoint webhook pour recevoir les notifications CamPay.
    CamPay envoie une notification POST quand le statut d'une transaction change.

    Sécurité :
    - Idempotence : si le paiement est déjà dans un état terminal, on ignore
    - Validation de structure du payload (external_reference obligatoire)
    - Aucune information sensible (clé API) n'est exposée dans les réponses
    - Les logs ne contiennent jamais de token ou clé API
    """

    # IPs officielles CamPay (à compléter si CamPay communique la liste)
    # Si vide → on ne filtre pas par IP (validation par structure payload)
    CAMPAY_WEBHOOK_IPS = []

    def post(self, request, *args, **kwargs):
        # ── Optionnel : filtrage par IP CamPay ─────────────────────────────
        if self.CAMPAY_WEBHOOK_IPS:
            client_ip = request.META.get('HTTP_X_FORWARDED_FOR', request.META.get('REMOTE_ADDR', ''))
            client_ip = client_ip.split(',')[0].strip()
            if client_ip not in self.CAMPAY_WEBHOOK_IPS:
                logger.warning(f"[CamPay Webhook] IP non autorisée: {client_ip}")
                return JsonResponse({'error': 'IP non autorisée'}, status=403)

        # ── Parsing du payload ──────────────────────────────────────────────
        try:
            data = json.loads(request.body)
        except json.JSONDecodeError:
            logger.warning("[CamPay Webhook] Payload JSON invalide")
            return JsonResponse({'error': 'JSON invalide'}, status=400)

        external_ref = data.get('external_reference', '').strip()
        campay_ref   = data.get('reference', '').strip()
        status_str   = data.get('status', '').upper()
        operator     = data.get('operator', '')

        # Log sans données sensibles (jamais la clé API)
        logger.info(
            f"[CamPay Webhook] Reçu — external_ref={external_ref}, "
            f"campay_ref={campay_ref}, status={status_str}, operator={operator}"
        )

        # ── Validation des champs obligatoires ─────────────────────────────
        if not external_ref:
            return JsonResponse({'error': 'external_reference manquant'}, status=400)
        if not status_str:
            return JsonResponse({'error': 'status manquant'}, status=400)

        # ── Recherche du paiement ──────────────────────────────────────────
        try:
            paiement = Paiement.objects.get(reference=external_ref)
        except Paiement.DoesNotExist:
            logger.warning(f"[CamPay Webhook] Paiement introuvable pour ref: {external_ref}")
            return JsonResponse({'error': 'Paiement introuvable'}, status=404)

        # ── Idempotence : ne pas retraiter un état final ───────────────────
        if paiement.is_terminal:
            logger.info(
                f"[CamPay Webhook] Paiement {external_ref} déjà terminal "
                f"({paiement.status}) — notification ignorée."
            )
            return JsonResponse({'status': 'already_processed'})

        # ── Mise à jour du statut ──────────────────────────────────────────
        internal_status = campay_service.CAMPAY_STATUS_MAP.get(status_str, 'pending')
        safe_data = campay_service._sanitize_raw_response(data)

        paiement.campay_reference    = campay_ref or paiement.campay_reference
        paiement.campay_operator     = operator or paiement.campay_operator
        paiement.campay_raw_response = safe_data
        paiement.status              = internal_status

        if internal_status == 'successful':
            paiement.paid_at = timezone.now()
            paiement.error_message = ''
        elif internal_status in ('failed', 'expired', 'cancelled'):
            paiement.error_message = campay_service._map_error_message(data, '')

        paiement.save()
        logger.info(f"[CamPay Webhook] Paiement {external_ref} → {internal_status}")
        return JsonResponse({'status': 'ok'})
