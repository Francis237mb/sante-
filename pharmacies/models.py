from django.db import models
from django.conf import settings

class PharmacyProfile(models.Model):
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='pharmacy_profile'
    )
    pharmacy_name = models.CharField(max_length=255, verbose_name="Nom de la pharmacie")
    address = models.CharField(max_length=255, verbose_name="Adresse")
    phone = models.CharField(max_length=50, blank=True, null=True, verbose_name="Téléphone")
    is_on_duty = models.BooleanField(default=False, verbose_name="Pharmacie de garde")
    opening_hours = models.CharField(max_length=100, default="08:00 - 22:00", verbose_name="Horaires d'ouverture")
    
    # Documents justificatifs
    registre_commerce = models.FileField(upload_to='pharmacy_documents/registres/', blank=True, null=True, verbose_name="Registre de commerce")
    autorisation_exercice = models.FileField(upload_to='pharmacy_documents/autorisations/', blank=True, null=True, verbose_name="Autorisation d'exercice")

    # Validation
    STATUS_PENDING = 'pending'
    STATUS_VERIFIED = 'verified'
    STATUS_REJECTED = 'rejected'
    VERIFICATION_STATUS_CHOICES = [
        (STATUS_PENDING, 'En attente'),
        (STATUS_VERIFIED, 'Validé'),
        (STATUS_REJECTED, 'Refusé'),
    ]
    is_verified = models.BooleanField(default=True, verbose_name="Compte validé par l'admin")
    verification_status = models.CharField(
        max_length=20,
        choices=VERIFICATION_STATUS_CHOICES,
        default=STATUS_VERIFIED,
        verbose_name="Statut de validation"
    )
    rejection_reason = models.TextField(blank=True, null=True, verbose_name="Motif du refus")
    submitted_at = models.DateTimeField(auto_now_add=True, null=True, blank=True, verbose_name="Date de demande")
    verified_at = models.DateTimeField(null=True, blank=True, verbose_name="Date de validation/rejet")

    def __str__(self):
        return self.pharmacy_name

class Medicament(models.Model):
    name = models.CharField(max_length=255, verbose_name="Nom du médicament")
    dosage = models.CharField(max_length=50, verbose_name="Dosage")
    description = models.TextField(blank=True, null=True, verbose_name="Indications / Description")
    price = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Prix (FCFA)")
    pharmacies = models.ManyToManyField(
        settings.AUTH_USER_MODEL,
        related_name='medicaments',
        limit_choices_to={'role': 'pharmacie'},
        verbose_name="Disponible dans ces pharmacies"
    )

    def __str__(self):
        return f"{self.name} {self.dosage}"
