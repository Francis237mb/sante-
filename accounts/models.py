from django.db import models
from django.contrib.auth.models import AbstractUser

class CustomUser(AbstractUser):
    PATIENT = 'patient'
    MEDECIN = 'medecin'
    PHARMACIE = 'pharmacie'
    ADMIN = 'admin'
    
    ROLE_CHOICES = [
        (PATIENT, 'Patient'),
        (MEDECIN, 'Médecin'),
        (PHARMACIE, 'Pharmacie'),
        (ADMIN, 'Administrateur'),
    ]
    
    role = models.CharField(
        max_length=20, 
        choices=ROLE_CHOICES, 
        default=PATIENT,
        verbose_name="Rôle"
    )
    phone_number = models.CharField(
        max_length=20, 
        blank=True, 
        null=True,
        verbose_name="Numéro de téléphone"
    )
    profile_picture = models.ImageField(
        upload_to='profiles/', 
        blank=True, 
        null=True,
        verbose_name="Photo de profil"
    )

    def __str__(self):
        return f"{self.username} ({self.get_role_display()})"
