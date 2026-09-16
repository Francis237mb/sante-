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

from datetime import datetime, timedelta
from django.contrib import messages

@login_required
def rejoindre_appel(request, rdv_id):
    rdv = get_object_or_404(RendezVous, id=rdv_id)
    
    # Vérifier que l'utilisateur est bien le patient ou le médecin du RDV
    if request.user != rdv.patient and request.user != rdv.doctor:
        return redirect('core:home')
        
    # S'assurer que le type de RDV est vidéo ou audio
    if rdv.consultation_type not in ['video', 'audio']:
        return redirect('core:home')

    # Vérification d'expiration de la salle (2 heures après le début prévu)
    try:
        hour, minute = map(int, rdv.time_slot.split(':'))
        rdv_datetime = datetime.combine(rdv.date, datetime.min.time()).replace(hour=hour, minute=minute)
        rdv_datetime = timezone.make_aware(rdv_datetime)
        
        if timezone.now() > rdv_datetime + timedelta(hours=2):
            messages.error(request, "Cette salle de consultation a expiré.")
            if request.user == rdv.patient:
                return redirect('consultations:patient_appointments')
            else:
                return redirect('medecins:dashboard')
    except Exception as e:
        pass

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

    is_doctor = (request.user == rdv.doctor)
    user_name = "Dr. " + request.user.get_full_name() if is_doctor else request.user.get_full_name()
    if not user_name.strip() or user_name.strip() == "Dr.":
        user_name = request.user.username

    context = {
        'appel': appel,
        'rdv': rdv,
        'room_code': str(appel.room_code),
        'user_name': user_name,
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
