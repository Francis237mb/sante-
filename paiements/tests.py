"""
Tests d'intégration CamPay — Fransick Santé
============================================
Couvre :
  1. normalize_phone() — tous les formats d'entrée
  2. detect_operator() — MTN, Orange, inconnu
  3. _map_error_message() — codes d'erreur -> messages lisibles
  4. should_expire_payment() — expiration automatique après 5 min
  5. Webhook CamPay — réception, idempotence, champs manquants
  6. CheckPaymentStatusAjaxView — polling, expiration, états terminaux

Exécution :
  python manage.py test paiements --verbosity=2
"""
import json
import uuid
from datetime import timedelta
from unittest.mock import patch, MagicMock

from django.contrib.auth import get_user_model
from django.test import TestCase, Client
from django.urls import reverse
from django.utils import timezone

from paiements.models import Paiement
from paiements.services import campay_service

User = get_user_model()


# ─────────────────────────────────────────────────────────────────────────────
# 1. NORMALISATION DU NUMÉRO DE TÉLÉPHONE
# ─────────────────────────────────────────────────────────────────────────────

class NormalizePhoneTestCase(TestCase):
    """Tests de normalize_phone() avec tous les formats d'entrée acceptés."""

    def test_format_court_9_chiffres(self):
        """677000000 -> 237677000000"""
        self.assertEqual(campay_service.normalize_phone('677000000'), '237677000000')

    def test_format_avec_indicatif_237(self):
        """237677000000 -> 237677000000 (inchangé)"""
        self.assertEqual(campay_service.normalize_phone('237677000000'), '237677000000')

    def test_format_plus_indicatif(self):
        """+237677000000 -> 237677000000"""
        self.assertEqual(campay_service.normalize_phone('+237677000000'), '237677000000')

    def test_format_00_indicatif(self):
        """00237677000000 -> 237677000000"""
        self.assertEqual(campay_service.normalize_phone('00237677000000'), '237677000000')

    def test_format_avec_espaces(self):
        """677 000 000 -> 237677000000"""
        self.assertEqual(campay_service.normalize_phone('677 000 000'), '237677000000')

    def test_format_avec_tirets(self):
        """677-000-000 -> 237677000000"""
        self.assertEqual(campay_service.normalize_phone('677-000-000'), '237677000000')

    def test_format_orange_court(self):
        """699000000 -> 237699000000"""
        self.assertEqual(campay_service.normalize_phone('699000000'), '237699000000')

    def test_strip_whitespace(self):
        """  677000000  -> 237677000000"""
        self.assertEqual(campay_service.normalize_phone('  677000000  '), '237677000000')


# ─────────────────────────────────────────────────────────────────────────────
# 2. DÉTECTION DE L'OPÉRATEUR
# ─────────────────────────────────────────────────────────────────────────────

class DetectOperatorTestCase(TestCase):
    """Tests de detect_operator() — préfixes MTN et Orange Cameroun."""

    # ── MTN ──────────────────────────────────────────────────────────────────
    def test_mtn_670(self):
        self.assertEqual(campay_service.detect_operator('670000000'), 'MTN')

    def test_mtn_677(self):
        self.assertEqual(campay_service.detect_operator('677000000'), 'MTN')

    def test_mtn_680(self):
        self.assertEqual(campay_service.detect_operator('680000000'), 'MTN')

    def test_mtn_689(self):
        self.assertEqual(campay_service.detect_operator('689000000'), 'MTN')

    def test_mtn_650(self):
        self.assertEqual(campay_service.detect_operator('650000000'), 'MTN')

    def test_mtn_654(self):
        self.assertEqual(campay_service.detect_operator('654000000'), 'MTN')

    # ── Orange ───────────────────────────────────────────────────────────────
    def test_orange_690(self):
        self.assertEqual(campay_service.detect_operator('690000000'), 'ORANGE')

    def test_orange_695(self):
        self.assertEqual(campay_service.detect_operator('695000000'), 'ORANGE')

    def test_orange_699(self):
        self.assertEqual(campay_service.detect_operator('699000000'), 'ORANGE')

    def test_orange_655(self):
        self.assertEqual(campay_service.detect_operator('655000000'), 'ORANGE')

    def test_orange_659(self):
        self.assertEqual(campay_service.detect_operator('659000000'), 'ORANGE')

    # ── Inconnu ──────────────────────────────────────────────────────────────
    def test_inconnu_retourne_vide(self):
        """Un préfixe non MTN/Orange doit retourner '' (CamPay détectera)."""
        result = campay_service.detect_operator('600000000')
        self.assertEqual(result, '')

    def test_avec_format_international(self):
        """Fonctionne aussi avec le format +237XXXXXXXXX."""
        self.assertEqual(campay_service.detect_operator('+237677000000'), 'MTN')


# ─────────────────────────────────────────────────────────────────────────────
# 3. MESSAGES D'ERREUR SPÉCIFIQUES
# ─────────────────────────────────────────────────────────────────────────────

class ErrorMessageMappingTestCase(TestCase):
    """Tests de _map_error_message() — codes CamPay -> messages lisibles."""

    def test_solde_insuffisant_par_code(self):
        data = {'error_code': 'insufficient_balance', 'message': 'Error'}
        msg = campay_service._map_error_message(data)
        self.assertIn('Solde', msg)

    def test_solde_insuffisant_par_mot_cle(self):
        data = {'message': 'Insufficient balance for this transaction'}
        msg = campay_service._map_error_message(data)
        self.assertIn('Solde', msg)

    def test_numero_invalide(self):
        data = {'error_code': 'invalid_phone', 'message': 'phone number is invalid'}
        msg = campay_service._map_error_message(data)
        self.assertIn('enregistré', msg)

    def test_annulation_utilisateur(self):
        data = {'error_code': 'user_cancelled'}
        msg = campay_service._map_error_message(data)
        self.assertIn('annulé', msg)

    def test_timeout(self):
        data = {'message': 'Transaction timeout expired'}
        msg = campay_service._map_error_message(data)
        self.assertIn('expiré', msg)

    def test_message_generique_si_aucun_code(self):
        data = {'message': 'Une erreur inconnue'}
        msg = campay_service._map_error_message(data)
        # Doit retourner quelque chose de lisible (pas vide)
        self.assertTrue(len(msg) > 5)

    def test_suppression_donnees_sensibles(self):
        """_sanitize_raw_response ne doit pas conserver les tokens."""
        data = {
            'reference': 'camp_123',
            'status': 'SUCCESSFUL',
            'token': 'SECRET_TOKEN_ABC',
            'access_token': 'another_secret',
            'amount': '5000',
        }
        safe = campay_service._sanitize_raw_response(data)
        self.assertNotIn('token', safe)
        self.assertNotIn('access_token', safe)
        self.assertIn('reference', safe)
        self.assertIn('amount', safe)


# ─────────────────────────────────────────────────────────────────────────────
# 4. EXPIRATION AUTOMATIQUE DES PAIEMENTS
# ─────────────────────────────────────────────────────────────────────────────

class PaymentExpiryTestCase(TestCase):
    """Tests de should_expire_payment() et de la propriété is_expired_pending."""

    def setUp(self):
        self.patient = User.objects.create_user(
            username='exppatient', password='testpass123', role='patient',
            email='exppatient@fransick.test'
        )
        self.medecin = User.objects.create_user(
            username='expdoctor', password='testpass123', role='medecin',
            email='expdoctor@fransick.test'
        )

    def _create_paiement(self, status='pending', minutes_ago=0):
        p = Paiement.objects.create(
            patient=self.patient,
            medecin=self.medecin,
            montant_total_consultation=10000,
            montant_paye=2000,
            phone_number='237677000000',
            status=status,
        )
        if minutes_ago > 0:
            # Forcer la date de création dans le passé
            Paiement.objects.filter(pk=p.pk).update(
                created_at=timezone.now() - timedelta(minutes=minutes_ago)
            )
            p.refresh_from_db()
        return p

    def test_paiement_frais_pas_expire(self):
        """Un paiement créé il y a 1 minute ne doit pas expirer."""
        p = self._create_paiement(minutes_ago=1)
        self.assertFalse(p.is_expired_pending)

    def test_paiement_vieux_expire(self):
        """Un paiement créé il y a 6 minutes doit être considéré expiré."""
        p = self._create_paiement(minutes_ago=6)
        self.assertTrue(p.is_expired_pending)

    def test_paiement_terminal_pas_expire(self):
        """Un paiement successful ne doit jamais retourner is_expired_pending=True."""
        p = self._create_paiement(status='successful', minutes_ago=10)
        self.assertFalse(p.is_expired_pending)

    def test_should_expire_function(self):
        """should_expire_payment() doit retourner True pour un paiement vieux de 6 min."""
        p = self._create_paiement(minutes_ago=6)
        self.assertTrue(campay_service.should_expire_payment(p))

    def test_is_terminal_property(self):
        """is_terminal retourne True pour tous les statuts finaux."""
        for status in ['successful', 'failed', 'expired', 'cancelled']:
            p = self._create_paiement(status=status)
            self.assertTrue(p.is_terminal, f"Statut '{status}' devrait être terminal")

    def test_pending_pas_terminal(self):
        p = self._create_paiement(status='pending')
        self.assertFalse(p.is_terminal)


# ─────────────────────────────────────────────────────────────────────────────
# 5. WEBHOOK CAMPAY
# ─────────────────────────────────────────────────────────────────────────────

class CamPayWebhookTestCase(TestCase):
    """Tests de l'endpoint webhook /paiements/webhook/campay/."""

    def setUp(self):
        self.client = Client()
        self.patient = User.objects.create_user(
            username='testpatient', password='testpass123', role='patient',
            email='testpatient@fransick.test'
        )
        self.medecin = User.objects.create_user(
            username='testdoctor', password='testpass123', role='medecin',
            email='testdoctor@fransick.test'
        )
        self.paiement = Paiement.objects.create(
            patient=self.patient,
            medecin=self.medecin,
            montant_total_consultation=10000,
            montant_paye=2000,
            phone_number='237677000000',
            status=Paiement.STATUS_PENDING,
            campay_reference='camp_test_ref_001',
        )
        self.webhook_url = reverse('paiements:campay_webhook')

    def _post_webhook(self, data):
        return self.client.post(
            self.webhook_url,
            data=json.dumps(data),
            content_type='application/json',
        )

    def test_webhook_paiement_successful(self):
        """Le webhook SUCCESSFUL doit marquer le paiement comme réussi."""
        resp = self._post_webhook({
            'external_reference': str(self.paiement.reference),
            'reference': 'camp_test_ref_001',
            'status': 'SUCCESSFUL',
            'operator': 'MTN',
        })
        self.assertEqual(resp.status_code, 200)
        self.paiement.refresh_from_db()
        self.assertEqual(self.paiement.status, Paiement.STATUS_SUCCESSFUL)
        self.assertIsNotNone(self.paiement.paid_at)
        print("[OK] Webhook SUCCESSFUL -> paiement marqué successful")

    def test_webhook_paiement_failed(self):
        """Le webhook FAILED doit marquer le paiement comme échoué."""
        resp = self._post_webhook({
            'external_reference': str(self.paiement.reference),
            'reference': 'camp_test_ref_001',
            'status': 'FAILED',
            'message': 'Insufficient balance',
        })
        self.assertEqual(resp.status_code, 200)
        self.paiement.refresh_from_db()
        self.assertEqual(self.paiement.status, Paiement.STATUS_FAILED)
        print("[OK] Webhook FAILED -> paiement marqué failed")

    def test_webhook_paiement_cancelled(self):
        """Le webhook CANCELLED doit marquer le paiement comme annulé."""
        resp = self._post_webhook({
            'external_reference': str(self.paiement.reference),
            'reference': 'camp_test_ref_001',
            'status': 'CANCELLED',
        })
        self.assertEqual(resp.status_code, 200)
        self.paiement.refresh_from_db()
        self.assertEqual(self.paiement.status, Paiement.STATUS_CANCELLED)
        print("[OK] Webhook CANCELLED -> paiement marqué cancelled")

    def test_webhook_idempotence(self):
        """Un second webhook sur un paiement déjà terminal doit être ignoré."""
        # Premier webhook -> successful
        self._post_webhook({
            'external_reference': str(self.paiement.reference),
            'status': 'SUCCESSFUL',
            'operator': 'MTN',
        })
        self.paiement.refresh_from_db()
        self.assertEqual(self.paiement.status, Paiement.STATUS_SUCCESSFUL)

        # Second webhook (FAILED) -> doit être ignoré
        resp = self._post_webhook({
            'external_reference': str(self.paiement.reference),
            'status': 'FAILED',
        })
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertEqual(data.get('status'), 'already_processed')
        self.paiement.refresh_from_db()
        # Toujours successful
        self.assertEqual(self.paiement.status, Paiement.STATUS_SUCCESSFUL)
        print("[OK] Webhook idempotent (pas de double traitement)")

    def test_webhook_external_reference_manquant(self):
        """Un webhook sans external_reference doit retourner 400."""
        resp = self._post_webhook({'status': 'SUCCESSFUL', 'reference': 'xyz'})
        self.assertEqual(resp.status_code, 400)
        print("[OK] Webhook sans external_reference -> 400")

    def test_webhook_paiement_introuvable(self):
        """Un webhook avec une référence inconnue doit retourner 404."""
        resp = self._post_webhook({
            'external_reference': str(uuid.uuid4()),
            'status': 'SUCCESSFUL',
        })
        self.assertEqual(resp.status_code, 404)
        print("[OK] Webhook paiement introuvable -> 404")

    def test_webhook_json_invalide(self):
        """Un payload non-JSON doit retourner 400."""
        resp = self.client.post(
            self.webhook_url,
            data='not json',
            content_type='application/json',
        )
        self.assertEqual(resp.status_code, 400)
        print("[OK] Webhook JSON invalide -> 400")

    def test_webhook_donnees_sensibles_non_stockees(self):
        """Les tokens ne doivent jamais être stockés dans campay_raw_response."""
        self._post_webhook({
            'external_reference': str(self.paiement.reference),
            'status': 'SUCCESSFUL',
            'token': 'SECRET_TOKEN_SHOULD_NOT_BE_STORED',
            'operator': 'ORANGE',
        })
        self.paiement.refresh_from_db()
        raw = self.paiement.campay_raw_response or {}
        self.assertNotIn('token', raw)
        print("[OK] Données sensibles (token) non stockées en DB")


# ─────────────────────────────────────────────────────────────────────────────
# 6. POLLING AJAX — EXPIRATION AUTOMATIQUE
# ─────────────────────────────────────────────────────────────────────────────

class PollingExpirationTestCase(TestCase):
    """Tests de CheckPaymentStatusAjaxView — expiration automatique."""

    def setUp(self):
        self.client = Client()
        self.patient = User.objects.create_user(
            username='pollpatient', password='testpass123', role='patient',
            email='pollpatient@fransick.test'
        )
        self.medecin = User.objects.create_user(
            username='polldoctor', password='testpass123', role='medecin',
            email='polldoctor@fransick.test'
        )
        self.client.login(username='pollpatient', password='testpass123')

    def _create_pending_payment(self, minutes_ago=0):
        p = Paiement.objects.create(
            patient=self.patient,
            medecin=self.medecin,
            montant_total_consultation=10000,
            montant_paye=2000,
            phone_number='237677000000',
            status=Paiement.STATUS_PENDING,
            campay_reference='camp_poll_ref_001',
        )
        if minutes_ago > 0:
            Paiement.objects.filter(pk=p.pk).update(
                created_at=timezone.now() - timedelta(minutes=minutes_ago)
            )
            p.refresh_from_db()
        return p

    def test_polling_expire_apres_5_minutes(self):
        """Le polling doit marquer le paiement comme expiré après 5 min de pending."""
        p = self._create_pending_payment(minutes_ago=6)
        url = reverse('paiements:check_status_ajax', kwargs={'paiement_ref': p.reference})
        resp = self.client.get(url, HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertEqual(data['status'], 'expired')
        p.refresh_from_db()
        self.assertEqual(p.status, Paiement.STATUS_EXPIRED)
        print("[OK] Paiement expiré automatiquement après 5 min")

    def test_polling_paiement_recent_reste_pending(self):
        """Un paiement récent (1 min) doit rester pending même sans réponse CamPay."""
        p = self._create_pending_payment(minutes_ago=1)
        # Simuler CamPay qui retourne PENDING
        with patch('paiements.services.campay_service.check_transaction_status') as mock:
            mock.return_value = {'status': 'PENDING', 'operator': '', 'message': '', 'raw': {}}
            url = reverse('paiements:check_status_ajax', kwargs={'paiement_ref': p.reference})
            resp = self.client.get(url, HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        data = resp.json()
        self.assertEqual(data['status'], 'pending')
        print("[OK] Paiement récent reste pending correctement")

    def test_polling_retourne_message_erreur_specifique(self):
        """Le polling doit retourner un message d'erreur spécifique quand failed."""
        p = self._create_pending_payment(minutes_ago=1)
        with patch('paiements.services.campay_service.check_transaction_status') as mock:
            mock.return_value = {
                'status': 'FAILED',
                'operator': '',
                'message': campay_service.CAMPAY_ERROR_MESSAGES['insufficient_balance'],
                'raw': {},
            }
            url = reverse('paiements:check_status_ajax', kwargs={'paiement_ref': p.reference})
            resp = self.client.get(url, HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        data = resp.json()
        self.assertEqual(data['status'], 'failed')
        self.assertIn('Solde', data.get('message', ''))
        print("[OK] Message d'erreur spécifique (solde) renvoyé au frontend")
