from django.db import models
from django.conf import settings
from django.core.exceptions import ValidationError
from django.contrib.contenttypes.models import ContentType
from django.contrib.contenttypes.fields import GenericForeignKey

class SiteAppearance(models.Model):
    app_name = models.CharField(max_length=100, default="Fransick", verbose_name="Nom de l'application")
    hero_text = models.CharField(max_length=200, default="La santé à portée de main", verbose_name="Texte d'accroche (Accueil)")
    hero_description = models.TextField(default="Gérez vos consultations, ordonnances et rendez-vous médicaux en un seul endroit.", verbose_name="Description courte (Accueil)")
    hero_image = models.ImageField(upload_to='appearance/', blank=True, null=True, verbose_name="Image principale (Accueil)")
    
    primary_color = models.CharField(max_length=7, default="#1B5FA8", verbose_name="Couleur principale (Hex)")
    secondary_color = models.CharField(max_length=7, default="#6DBE45", verbose_name="Couleur secondaire (Hex)")
    logo = models.ImageField(upload_to='appearance/', blank=True, null=True, verbose_name="Logo")
    favicon = models.ImageField(upload_to='appearance/', blank=True, null=True, verbose_name="Favicon")
    
    # Réseaux sociaux
    facebook_url = models.URLField(blank=True, null=True, verbose_name="Lien Facebook")
    twitter_url = models.URLField(blank=True, null=True, verbose_name="Lien Twitter (X)")
    instagram_url = models.URLField(blank=True, null=True, verbose_name="Lien Instagram")
    linkedin_url = models.URLField(blank=True, null=True, verbose_name="Lien LinkedIn")
    
    # Informations de contact
    contact_email = models.EmailField(default="support@fransick.com", verbose_name="Email de contact")
    contact_phone = models.CharField(max_length=20, default="+33 1 23 45 67 89", verbose_name="Téléphone de contact")
    contact_address = models.CharField(max_length=255, default="123 Rue de la Santé, 75000 Paris", verbose_name="Adresse de contact")
    
    # Fonctionnalités (Toggles)
    maintenance_mode = models.BooleanField(default=False, verbose_name="Mode maintenance (désactive l'accès aux utilisateurs non-admins)")
    enable_ia_assistant = models.BooleanField(default=True, verbose_name="Activer l'assistant IA")
    enable_payments = models.BooleanField(default=False, verbose_name="Activer le module de paiement (si disponible)")
    report_suspension_threshold = models.PositiveIntegerField(default=6, verbose_name="Seuil de signalements pour suspension auto")
    
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Apparence du site"
        verbose_name_plural = "Apparence du site"

    def clean(self):
        # S'assurer qu'il n'y a qu'une seule instance
        if SiteAppearance.objects.exists() and not self.pk:
            raise ValidationError("Il ne peut y avoir qu'une seule configuration d'apparence. Veuillez modifier celle existante.")

    def __str__(self):
        return "Configuration de l'apparence"

class StaticPage(models.Model):
    PAGE_CHOICES = [
        ('about', 'À propos'),
        ('cgu', 'Conditions Générales d\'Utilisation'),
        ('privacy', 'Politique de Confidentialité'),
    ]
    page_type = models.CharField(max_length=20, choices=PAGE_CHOICES, unique=True, verbose_name="Type de page")
    title = models.CharField(max_length=200, verbose_name="Titre de la page")
    content = models.TextField(verbose_name="Contenu HTML")
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Page Statique"
        verbose_name_plural = "Pages Statiques"

    def __str__(self):
        return self.get_page_type_display()

class Report(models.Model):
    STATUS_CHOICES = [
        ('new', 'Nouveau'),
        ('in_progress', 'En cours'),
        ('resolved', 'Résolu'),
    ]
    REPORT_TYPE_CHOICES = [
        ('technique', 'Problème technique'),
        ('comportement', 'Comportement utilisateur'),
        ('litige', 'Litige de commande/consultation'),
        ('autre', 'Autre'),
    ]
    author = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='reports_created', verbose_name="Signalé par")
    target_user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='reports_received', null=True, blank=True, verbose_name="Utilisateur signalé")
    report_type = models.CharField(max_length=50, choices=REPORT_TYPE_CHOICES, default='autre', verbose_name="Type de signalement")
    title = models.CharField(max_length=200, verbose_name="Titre du signalement")
    description = models.TextField(verbose_name="Description détaillée")
    attachment = models.FileField(upload_to='reports/attachments/', blank=True, null=True, verbose_name="Pièce jointe")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='new', verbose_name="Statut")
    admin_response = models.TextField(blank=True, null=True, verbose_name="Réponse de l'administration")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Signalement"
        verbose_name_plural = "Signalements"
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.title} - {self.get_status_display()}"

class ActivityLog(models.Model):
    ACTION_TYPES = [
        ('connexion', 'Connexion / Déconnexion'),
        ('inscription', 'Inscription'),
        ('profil', 'Modification de profil'),
        ('recherche', 'Recherche de médecin'),
        ('consultation', 'Consultation (RDV)'),
        ('ordonnance', 'Ordonnance'),
        ('document', 'Document justificatif'),
        ('catalogue', 'Catalogue de pharmacie'),
        ('ia', 'Assistant IA'),
        ('signalement', 'Signalement'),
        ('admin', 'Action Administrateur'),
        ('autre', 'Autre'),
    ]
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, null=True, blank=True, related_name='activity_logs', verbose_name="Utilisateur")
    action_type = models.CharField(max_length=50, choices=ACTION_TYPES, default='autre', verbose_name="Type d'action")
    action = models.CharField(max_length=255, verbose_name="Description de l'action")
    
    # Lien optionnel vers un objet spécifique (ex: l'ordonnance générée, le profil modifié)
    content_type = models.ForeignKey(ContentType, on_delete=models.SET_NULL, null=True, blank=True)
    object_id = models.PositiveIntegerField(null=True, blank=True)
    content_object = GenericForeignKey('content_type', 'object_id')
    
    ip_address = models.GenericIPAddressField(blank=True, null=True, verbose_name="Adresse IP")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Journal d'activité"
        verbose_name_plural = "Journaux d'activité"
        ordering = ['-created_at']

    def __str__(self):
        user_str = self.user.username if self.user else "Utilisateur anonyme"
        return f"{user_str} - {self.action} à {self.created_at.strftime('%Y-%m-%d %H:%M')}"

from django.db.models.signals import post_save
from django.dispatch import receiver

@receiver(post_save, sender=Report)
def check_report_suspension(sender, instance, created, **kwargs):
    """
    Vérifie si l'utilisateur ciblé par le signalement a atteint le seuil
    maximum de signalements non-résolus. Si oui, on suspend son compte.
    """
    if created and instance.target_user and instance.target_user.is_active:
        appearance = SiteAppearance.objects.first()
        threshold = appearance.report_suspension_threshold if appearance else 6
        
        active_reports_count = Report.objects.filter(
            target_user=instance.target_user
        ).exclude(status='resolved').count()
        
        if active_reports_count >= threshold:
            instance.target_user.is_active = False
            instance.target_user.save()
            
            ActivityLog.objects.create(
                action=f"Suspension automatique (seuil de {threshold} signalements atteint)",
                action_type='admin',
                content_object=instance.target_user
            )
