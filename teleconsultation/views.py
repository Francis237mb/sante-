from django.shortcuts import render, get_object_or_404, redirect
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from django.conf import settings
from django.utils import timezone
from consultations.models import RendezVous
from administration.models import ActivityLog
from .models import AppelConsultation
from agora_token_builder import RtcTokenBuilder
import time

@login_required
def rejoindre_appel(request, rdv_id):
    rdv = get_object_or_404(RendezVous, id=rdv_id)
    
    # Vérifier que l'utilisateur est bien le patient ou le médecin du RDV
    if request.user != rdv.patient and request.user != rdv.doctor:
        return redirect('core:home') # ou une page d'erreur
        
    # S'assurer que le type de RDV est vidéo ou audio (bien que le modèle permette les 3)
    if rdv.consultation_type not in ['video', 'audio']:
        return redirect('core:home')

    appel, created = AppelConsultation.objects.get_or_create(
        rendez_vous=rdv,
        defaults={'status': 'en_attente'}
    )
    
    if appel.status == 'en_attente':
        appel.status = 'en_cours'
        appel.started_at = timezone.now()
        appel.save()
        
    # Mettre à jour le statut du RDV si ce n'est pas déjà fait
    if rdv.status != 'in_progress':
        rdv.status = 'in_progress'
        rdv.save()

    # Génération du token Agora
    app_id = settings.AGORA_APP_ID
    app_certificate = settings.AGORA_APP_CERTIFICATE
    channel_name = str(appel.channel_name)
    uid = request.user.id
    expiration_time_in_seconds = 3600 # 1 heure
    current_timestamp = int(time.time())
    privilege_expired_ts = current_timestamp + expiration_time_in_seconds
    role = 1 # Role_Publisher

    token = RtcTokenBuilder.buildTokenWithUid(
        app_id, app_certificate, channel_name, uid, role, privilege_expired_ts
    )

    is_doctor = (request.user == rdv.doctor)

    context = {
        'appel': appel,
        'rdv': rdv,
        'agora_app_id': app_id,
        'agora_token': token,
        'agora_channel': channel_name,
        'agora_uid': uid,
        'is_doctor': is_doctor
    }
    
    return render(request, 'teleconsultation/appel.html', context)

@login_required
def terminer_appel(request, appel_id):
    if request.method == 'POST':
        appel = get_object_or_404(AppelConsultation, id=appel_id)
        rdv = appel.rendez_vous
        
        # Vérification des droits
        if request.user != rdv.patient and request.user != rdv.doctor:
            return JsonResponse({'status': 'error', 'message': 'Non autorisé'}, status=403)
            
        # Mettre à jour l'appel
        if appel.status != 'termine':
            appel.status = 'termine'
            appel.ended_at = timezone.now()
            appel.save()
            
            # Mettre à jour le RDV
            rdv.status = 'completed'
            rdv.save()
            
            # Calcul de la durée si possible
            duree_str = "Durée inconnue"
            if appel.started_at and appel.ended_at:
                delta = appel.ended_at - appel.started_at
                minutes = int(delta.total_seconds() / 60)
                duree_str = f"{minutes} min"

            # Enregistrer dans l'ActivityLog
            ActivityLog.objects.create(
                user=request.user,
                action_type='consultation',
                action=f"Appel vidéo terminé pour le RDV #{rdv.id} ({duree_str})",
                content_object=rdv
            )
            
        return JsonResponse({'status': 'success'})
    return JsonResponse({'status': 'error', 'message': 'Méthode non autorisée'}, status=405)
