from django.db import models
from django.conf import settings

class RendezVous(models.Model):
    CONSULTATION_TYPES = [
        ('video', 'Téléconsultation Vidéo 🎥'),
        ('audio', 'Téléconsultation Audio 🎙️'),
        ('cabinet', 'Consultation en Cabinet 🏥'),
    ]

    STATUS_CHOICES = [
        ('confirmed', 'Confirmé'),
        ('pending', 'En attente'),
        ('completed', 'Terminé'),
        ('cancelled', 'Annulé'),
    ]

    patient = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='patient_appointments'
    )
    doctor = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='doctor_appointments'
    )
    consultation_type = models.CharField(
        max_length=20,
        choices=CONSULTATION_TYPES,
        default='video',
        verbose_name="Type de consultation"
    )
    date = models.DateField(verbose_name="Date du RDV")
    time_slot = models.CharField(max_length=20, verbose_name="Créneau horaire (ex: 10:00)")
    reason = models.CharField(max_length=255, verbose_name="Motif de la consultation")
    notes = models.TextField(blank=True, null=True, verbose_name="Symptômes / Remarques du patient")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='confirmed')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['date', 'time_slot']

    def __str__(self):
        return f"RDV {self.get_consultation_type_display()} le {self.date} à {self.time_slot} avec Dr. {self.doctor.username}"
