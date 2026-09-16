from django.contrib.auth.signals import user_logged_in, user_logged_out
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.conf import settings
from .models import ActivityLog
from ordonnances.models import Ordonnance
from accounts.models import CustomUser

@receiver(user_logged_in)
def log_user_login(sender, request, user, **kwargs):
    ip = request.META.get('REMOTE_ADDR')
    ActivityLog.objects.create(
        user=user,
        action="L'utilisateur s'est connecté",
        action_type='connexion',
        ip_address=ip
    )

@receiver(user_logged_out)
def log_user_logout(sender, request, user, **kwargs):
    if user:
        ip = request.META.get('REMOTE_ADDR')
        ActivityLog.objects.create(
            user=user,
            action="L'utilisateur s'est déconnecté",
            action_type='connexion',
            ip_address=ip
        )

@receiver(post_save, sender=CustomUser)
def log_user_registration(sender, instance, created, **kwargs):
    if created:
        ActivityLog.objects.create(
            user=instance,
            action=f"Inscription de l'utilisateur ({instance.get_role_display()})",
            action_type='inscription',
            content_object=instance
        )

@receiver(post_save, sender=Ordonnance)
def log_ordonnance_creation(sender, instance, created, **kwargs):
    if created:
        ActivityLog.objects.create(
            user=instance.doctor,
            action=f"Création d'une ordonnance pour {instance.patient.username if instance.patient else 'un patient'}",
            action_type='ordonnance',
            content_object=instance
        )
