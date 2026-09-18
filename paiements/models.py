from django.db import models
from django.conf import settings
from consultations.models import RendezVous
import uuid


class Paiement(models.Model):
    """Modèle représentant un paiement enregistré sur la plateforme."""

    # Types de paiement
    TYPE_ACOMPTE = 'acompte'
    TYPE_TOTAL = 'total'
    PAYMENT_TYPE_CHOICES = [
        (TYPE_ACOMPTE, 'Acompte RDV (20%)'),
        (TYPE_TOTAL, 'Paiement Total (Consultation Directe)'),
    ]

    # Statuts CamPay
    STATUS_PENDING = 'pending'
    STATUS_SUCCESSFUL = 'successful'
    STATUS_FAILED = 'failed'
    STATUS_EXPIRED = 'expired'
    STATUS_CANCELLED = 'cancelled'
    STATUS_CHOICES = [
        (STATUS_PENDING, 'En attente'),
        (STATUS_SUCCESSFUL, 'Succès'),
        (STATUS_FAILED, 'Échoué'),
        (STATUS_EXPIRED, 'Expiré'),
        (STATUS_CANCELLED, 'Annulé par le patient'),
    ]

    # Identification interne
    reference = models.UUIDField(
        default=uuid.uuid4, unique=True, editable=False,
        verbose_name="Référence interne"
    )

    # Liens vers les acteurs
    patient = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='paiements_effectues',
        verbose_name="Patient payeur"
    )
    medecin = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='paiements_recus',
        verbose_name="Médecin bénéficiaire"
    )
    rdv = models.ForeignKey(
        RendezVous,
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='paiements',
        verbose_name="Rendez-vous lié"
    )

    # Montants
    montant_total_consultation = models.DecimalField(
        max_digits=10, decimal_places=0,
        verbose_name="Tarif total de la consultation (XAF)"
    )
    montant_paye = models.DecimalField(
        max_digits=10, decimal_places=0,
        verbose_name="Montant réellement débité (XAF)"
    )
    pourcentage_acompte = models.PositiveIntegerField(
        default=20,
        verbose_name="Pourcentage d'acompte"
    )

    # Type et statut
    payment_type = models.CharField(
        max_length=20,
        choices=PAYMENT_TYPE_CHOICES,
        default=TYPE_ACOMPTE,
        verbose_name="Type de paiement"
    )
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default=STATUS_PENDING,
        verbose_name="Statut du paiement"
    )

    # Informations CamPay
    phone_number = models.CharField(
        max_length=20,
        verbose_name="Numéro Mobile Money du payeur"
    )
    campay_reference = models.CharField(
        max_length=255, blank=True, null=True,
        verbose_name="Référence CamPay (transaction)"
    )
    campay_operator = models.CharField(
        max_length=50, blank=True, null=True,
        verbose_name="Opérateur (MTN/Orange)"
    )
    campay_raw_response = models.JSONField(
        blank=True, null=True,
        verbose_name="Réponse brute CamPay (nettoyée, sans données sensibles)"
    )
    error_message = models.CharField(
        max_length=500, blank=True, default='',
        verbose_name="Message d'erreur (lisible patient)"
    )

    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Date de création")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Dernière mise à jour")
    paid_at = models.DateTimeField(null=True, blank=True, verbose_name="Date de paiement confirmé")

    class Meta:
        verbose_name = "Paiement"
        verbose_name_plural = "Paiements"
        ordering = ['-created_at']

    def __str__(self):
        return (
            f"Paiement {self.get_payment_type_display()} — "
            f"{self.montant_paye} XAF — {self.patient.username} "
            f"→ Dr.{self.medecin.username} [{self.get_status_display()}]"
        )

    @property
    def is_successful(self):
        return self.status == self.STATUS_SUCCESSFUL

    @property
    def is_pending(self):
        return self.status == self.STATUS_PENDING

    @property
    def is_cancelled(self):
        return self.status == self.STATUS_CANCELLED

    @property
    def is_terminal(self):
        """Retourne True si le paiement est dans un état final (non modifiable)."""
        return self.status in [
            self.STATUS_SUCCESSFUL, self.STATUS_FAILED,
            self.STATUS_EXPIRED, self.STATUS_CANCELLED,
        ]

    @property
    def is_expired_pending(self):
        """
        Retourne True si le paiement est resté pending depuis plus de 5 minutes.
        Utilisé pour déclencher l'expiration automatique côté polling.
        """
        import datetime
        from django.utils import timezone
        if self.status != self.STATUS_PENDING:
            return False
        return timezone.now() - self.created_at > datetime.timedelta(minutes=5)
