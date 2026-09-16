from django.db import models
from consultations.models import RendezVous
import uuid

class AppelConsultation(models.Model):
    STATUS_CHOICES = [
        ('en_attente', 'En attente'),
        ('en_cours', 'En cours'),
        ('termine', 'Terminé'),
    ]

    rendez_vous = models.OneToOneField(
        RendezVous,
        on_delete=models.CASCADE,
        related_name='appel_video',
        verbose_name="Rendez-vous associé"
    )
    room_code = models.CharField(
        max_length=100, 
        unique=True, 
        default=uuid.uuid4, 
        verbose_name="Code de la salle Jitsi"
    )
    status = models.CharField(
        max_length=20, 
        choices=STATUS_CHOICES, 
        default='en_attente', 
        verbose_name="Statut de l'appel"
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    started_at = models.DateTimeField(null=True, blank=True)
    ended_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        verbose_name = "Appel Vidéo"
        verbose_name_plural = "Appels Vidéo"

    def __str__(self):
        return f"Appel {self.room_code} pour RDV {self.rendez_vous.id}"
