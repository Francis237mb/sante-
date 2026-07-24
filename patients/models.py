from django.db import models
from django.conf import settings

class PatientProfile(models.Model):
    GENDER_CHOICES = [
        ('M', 'Masculin'),
        ('F', 'Féminin'),
        ('O', 'Autre'),
    ]
    
    CIVIL_STATUS_CHOICES = [
        ('celibataire', 'Célibataire'),
        ('marie', 'Marié'),
        ('divorce', 'Divorcé'),
        ('veuf', 'Veuf'),
    ]
    
    BLOOD_GROUP_CHOICES = [
        ('A+', 'A+'),
        ('A-', 'A-'),
        ('B+', 'B+'),
        ('B-', 'B-'),
        ('AB+', 'AB+'),
        ('AB-', 'AB-'),
        ('O+', 'O+'),
        ('O-', 'O-'),
    ]

    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='patient_profile'
    )
    gender = models.CharField(
        max_length=10,
        choices=GENDER_CHOICES,
        blank=True,
        null=True,
        verbose_name="Sexe"
    )
    additional_notes = models.TextField(
        blank=True,
        null=True,
        verbose_name="Notes supplémentaires (allergie, diabétique...)"
    )
    city = models.CharField(
        max_length=100,
        blank=True,
        null=True,
        verbose_name="Ville"
    )
    neighborhood = models.CharField(
        max_length=100,
        blank=True,
        null=True,
        verbose_name="Quartier"
    )
    occupation = models.CharField(
        max_length=150,
        blank=True,
        null=True,
        verbose_name="Occupation"
    )
    civil_status = models.CharField(
        max_length=20,
        choices=CIVIL_STATUS_CHOICES,
        blank=True,
        null=True,
        verbose_name="État civil"
    )
    height = models.PositiveIntegerField(
        blank=True,
        null=True,
        verbose_name="Taille (en cm)"
    )
    weight = models.PositiveIntegerField(
        blank=True,
        null=True,
        verbose_name="Poids (en Kg)"
    )
    blood_group = models.CharField(
        max_length=10,
        choices=BLOOD_GROUP_CHOICES,
        blank=True,
        null=True,
        verbose_name="Groupe sanguin"
    )

    def __str__(self):
        return f"Profil de {self.user.username}"
