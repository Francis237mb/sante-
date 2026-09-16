from django.db import models
from django.conf import settings

class Specialite(models.Model):
    name = models.CharField(max_length=150, unique=True, verbose_name="Nom de la spécialité")
    icon = models.ImageField(upload_to='specialities/icons/', blank=True, null=True, verbose_name="Icône")
    description = models.TextField(blank=True, null=True, verbose_name="Description")
    
    class Meta:
        verbose_name = "Spécialité médicale"
        verbose_name_plural = "Spécialités médicales"
        ordering = ['name']

    def __str__(self):
        return self.name

class DoctorProfile(models.Model):
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='doctor_profile'
    )
    speciality = models.CharField(max_length=150, blank=True, null=True, verbose_name="Spécialité médicale (Ancien)")
    specialite = models.ForeignKey(Specialite, on_delete=models.SET_NULL, null=True, blank=True, verbose_name="Spécialité médicale")
    license_number = models.CharField(max_length=100, unique=True, blank=True, null=True, verbose_name="Numéro de licence / ordre")
    about = models.TextField(blank=True, null=True, verbose_name="Présentation / Biographie")
    schedule = models.CharField(max_length=255, blank=True, null=True, verbose_name="Horaires de consultation")
    years_of_experience = models.PositiveIntegerField(blank=True, null=True, verbose_name="Années d'expérience")
    consulted_patients_count = models.PositiveIntegerField(blank=True, null=True, verbose_name="Nombre de patients consultés")
    clinic_name = models.CharField(max_length=255, blank=True, null=True, verbose_name="Nom de la clinique / cabinet")
    clinic_address = models.CharField(max_length=255, blank=True, null=True, verbose_name="Adresse du cabinet")
    clinic_phone = models.CharField(max_length=50, blank=True, null=True, verbose_name="Téléphone du cabinet")
    rating = models.DecimalField(max_digits=3, decimal_places=1, default=0.0, verbose_name="Note moyenne")
    consultation_fee = models.DecimalField(
        max_digits=10, decimal_places=0,
        blank=True, null=True,
        verbose_name="Tarif de consultation (XAF)"
    )

    # Étape 2 : Informations Professionnelles
    address = models.CharField(max_length=255, blank=True, null=True, verbose_name="Adresse complète")
    city = models.CharField(max_length=100, blank=True, null=True, verbose_name="Ville")
    region = models.CharField(max_length=100, blank=True, null=True, verbose_name="Région")
    hospital_affiliation = models.CharField(max_length=255, blank=True, null=True, verbose_name="Hôpital / structure d'exercice")

    # Étape 3 : Documents justificatifs (téléversement)
    diploma_document = models.FileField(upload_to='doctor_documents/diplomas/', blank=True, null=True, verbose_name="Diplôme(s) médical(aux)")
    professional_card_document = models.FileField(upload_to='doctor_documents/cards/', blank=True, null=True, verbose_name="Carte professionnelle / Attestation Ordre")
    identity_document = models.FileField(upload_to='doctor_documents/identity/', blank=True, null=True, verbose_name="Pièce d'identité")

    # Statut et flux de validation administratives
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
        return f"Profil du Dr. {self.user.username} ({self.get_verification_status_display()})"


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


class VideoComment(models.Model):
    video = models.ForeignKey(
        HealthVideo, 
        on_delete=models.CASCADE, 
        related_name='comments'
    )
    author = models.ForeignKey(
        settings.AUTH_USER_MODEL, 
        on_delete=models.CASCADE, 
        related_name='video_comments'
    )
    text = models.TextField(verbose_name="Commentaire")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Date du commentaire")

    class Meta:
        ordering = ['created_at']

    def __str__(self):
        return f"Commentaire de {self.author.username} sur {self.video.title}"

