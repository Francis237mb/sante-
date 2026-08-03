from django.db import models
from django.conf import settings
from consultations.models import RendezVous

class Ordonnance(models.Model):
    rendez_vous = models.OneToOneField(
        RendezVous,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='ordonnance',
        verbose_name="Rendez-vous associé"
    )
    doctor = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='doctor_prescriptions',
        verbose_name="Médecin prescripteur"
    )
    patient = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='patient_prescriptions',
        verbose_name="Patient"
    )
    patient_age = models.CharField(max_length=20, default="30 ans", verbose_name="Âge du patient")
    diagnostic = models.TextField(verbose_name="Diagnostic Médical")
    prescription_details = models.TextField(verbose_name="Prescriptions / Médicaments (Rx)")
    date = models.DateField(auto_now_add=True, verbose_name="Date d'émission")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = "Ordonnance"
        verbose_name_plural = "Ordonnances"

    def __str__(self):
        return f"Ordonnance #{self.id} - Dr. {self.doctor.username} pour {self.patient.username}"

