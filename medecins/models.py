from django.db import models
from django.conf import settings

class DoctorProfile(models.Model):
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='doctor_profile'
    )
    speciality = models.CharField(max_length=150, blank=True, null=True, verbose_name="Spécialité médicale")
    license_number = models.CharField(max_length=100, blank=True, null=True, verbose_name="Numéro de licence / ordre")
    about = models.TextField(blank=True, null=True, verbose_name="Présentation / Biographie")
    schedule = models.CharField(max_length=255, blank=True, null=True, verbose_name="Horaires de consultation")
    years_of_experience = models.PositiveIntegerField(blank=True, null=True, verbose_name="Années d'expérience")
    consulted_patients_count = models.PositiveIntegerField(blank=True, null=True, verbose_name="Nombre de patients consultés")
    clinic_name = models.CharField(max_length=255, blank=True, null=True, verbose_name="Nom de la clinique / cabinet")
    clinic_address = models.CharField(max_length=255, blank=True, null=True, verbose_name="Adresse du cabinet")
    clinic_phone = models.CharField(max_length=50, blank=True, null=True, verbose_name="Téléphone du cabinet")
    rating = models.DecimalField(max_digits=3, decimal_places=1, default=5.0, verbose_name="Note moyenne")

    def __str__(self):
        return f"Profil du Dr. {self.user.username}"


class DoctorSubscription(models.Model):
    patient = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='subscriptions_given'
    )
    doctor = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='subscribers_received'
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('patient', 'doctor')

    def __str__(self):
        return f"{self.patient.username} abonné à Dr. {self.doctor.username}"


class HealthVideo(models.Model):
    author = models.ForeignKey(
        settings.AUTH_USER_MODEL, 
        on_delete=models.CASCADE, 
        related_name='published_videos'
    )
    title = models.CharField(max_length=255, verbose_name="Titre de la capsule")
    description = models.TextField(blank=True, null=True, verbose_name="Légende & Hashtags")
    video_file = models.FileField(upload_to='videos/', blank=True, null=True, verbose_name="Fichier vidéo")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Date de publication")
    likes_count = models.PositiveIntegerField(default=0, verbose_name="Nombre de réactions")

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.title} par {self.author.username}"
