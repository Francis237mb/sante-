from django.views.generic import TemplateView, View
from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse
from django.contrib import messages
from django.utils.crypto import get_random_string
from .models import RendezVous

class ConsultationListView(LoginRequiredMixin, TemplateView):
    template_name = 'consultations/list.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        if getattr(self.request.user, 'role', '') == 'medecin':
            rdvs = RendezVous.objects.filter(doctor=self.request.user).select_related('patient').order_by('-date', '-time_slot')
            context['is_doctor'] = True
        else:
            rdvs = RendezVous.objects.filter(patient=self.request.user).select_related('doctor').order_by('-date', '-time_slot')
            context['is_doctor'] = False
        
        context['all_rdvs'] = rdvs
        context['pending_rdvs'] = rdvs.filter(status='pending')
        context['confirmed_rdvs'] = rdvs.filter(status='confirmed')
        context['cancelled_rdvs'] = rdvs.filter(status='cancelled')
        return context

class JoinWaitingRoomView(LoginRequiredMixin, View):
    def post(self, request, pk, *args, **kwargs):
        rdv = get_object_or_404(RendezVous, pk=pk, patient=request.user)
        # Activer la salle d'attente
        rdv.in_waiting_room = True
        if not rdv.room_name:
            # Générer un nom de salon unique et sécurisé
            rdv.room_name = f"fransick_teleconsult_{rdv.id}_{get_random_string(8)}"
        rdv.save()
        return redirect('consultations:patient_waiting_room', pk=rdv.id)

class PatientWaitingRoomView(LoginRequiredMixin, TemplateView):
    template_name = 'consultations/waiting_room.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        rdv_id = self.kwargs.get('pk')
        context['rdv'] = get_object_or_404(RendezVous, pk=rdv_id, patient=self.request.user)
        return context

class CheckRdvStatusView(LoginRequiredMixin, View):
    def get(self, request, pk, *args, **kwargs):
        rdv = get_object_or_404(RendezVous, pk=pk)
        if request.user != rdv.patient and request.user != rdv.doctor:
            return JsonResponse({'status': 'error', 'message': 'Accès refusé'}, status=403)
        return JsonResponse({
            'status': rdv.status,
            'in_waiting_room': rdv.in_waiting_room,
            'room_name': rdv.room_name,
        })

class DoctorWaitingRoomListView(LoginRequiredMixin, View):
    def get(self, request, *args, **kwargs):
        # Récupérer les rdv du médecin connecté qui patientent dans la salle d'attente
        rdvs = RendezVous.objects.filter(
            doctor=request.user, 
            in_waiting_room=True, 
            status__in=['confirmed', 'pending']
        )
        data = []
        for rdv in rdvs:
            data.append({
                'id': rdv.id,
                'patient_name': rdv.patient.username,
                'patient_avatar': rdv.patient.profile_picture.url if rdv.patient.profile_picture else None,
                'patient_initials': rdv.patient.username[:2].upper(),
                'time_slot': rdv.time_slot,
                'reason': rdv.reason,
                'type': rdv.get_consultation_type_display(),
            })
        return JsonResponse({'waiting_patients': data})

class StartConsultationView(LoginRequiredMixin, View):
    def post(self, request, pk, *args, **kwargs):
        rdv = get_object_or_404(RendezVous, pk=pk, doctor=request.user)
        # Admettre le patient et démarrer la consultation
        rdv.in_waiting_room = False
        rdv.status = 'in_progress'
        if not rdv.room_name:
            rdv.room_name = f"fransick_teleconsult_{rdv.id}_{get_random_string(8)}"
        rdv.save()
        return redirect('teleconsultation:rejoindre_appel', rdv_id=rdv.id)

class ConsultationRoomView(LoginRequiredMixin, TemplateView):
    template_name = 'consultations/consultation_room.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        rdv_id = self.kwargs.get('pk')
        # Accessible si l'utilisateur est soit le médecin, soit le patient du rdv
        rdv = get_object_or_404(RendezVous, pk=rdv_id)
        if self.request.user != rdv.patient and self.request.user != rdv.doctor:
            raise PermissionError("Accès interdit à ce salon de consultation.")
        context['rdv'] = rdv
        return context

class EndConsultationView(LoginRequiredMixin, View):
    def post(self, request, pk, *args, **kwargs):
        rdv = get_object_or_404(RendezVous, pk=pk)
        if request.user != rdv.patient and request.user != rdv.doctor:
            return JsonResponse({'status': 'error', 'message': 'Permission refusée'}, status=403)
            
        rdv.status = 'completed'
        rdv.in_waiting_room = False
        rdv.save()
        
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest' or request.content_type == 'application/json':
            redirect_url = f"/ordonnances/creer/{rdv.id}/" if request.user.role == 'medecin' else "/patients/dashboard/"
            return JsonResponse({'status': 'success', 'redirect_url': redirect_url})
            
        messages.success(request, "La consultation a été terminée avec succès.")
        if request.user.role == 'medecin':
            return redirect('ordonnances:create_for_rdv', rdv_id=rdv.id)
        return redirect('patients:dashboard')

class CreateDirectConsultationView(LoginRequiredMixin, View):
    def post(self, request, *args, **kwargs):
        import json
        import datetime
        from django.contrib.auth import get_user_model
        User = get_user_model()
        try:
            data = json.loads(request.body)
            doctor_id = data.get('doctor_id')
            consultation_type = data.get('consultation_type', 'video')
            
            doctor = get_object_or_404(User, pk=doctor_id, role='medecin')
            
            now = datetime.datetime.now()
            time_slot = now.strftime("%H:%M")
            
            rdv = RendezVous.objects.create(
                patient=request.user,
                doctor=doctor,
                consultation_type=consultation_type,
                date=datetime.date.today(),
                time_slot=time_slot,
                reason="Téléconsultation Directe",
                status='confirmed',
                in_waiting_room=True,
                room_name=f"fransick_teleconsult_direct_{request.user.id}_{get_random_string(8)}"
            )
            return JsonResponse({'status': 'success', 'rdv_id': rdv.id})
        except Exception as e:
            return JsonResponse({'status': 'error', 'message': str(e)}, status=400)


class AcceptAppointmentView(LoginRequiredMixin, View):
    def post(self, request, pk, *args, **kwargs):
        rdv = get_object_or_404(RendezVous, pk=pk)
        # Seul le médecin concerné (ou un admin) peut valider
        if request.user != rdv.doctor and not request.user.is_superuser:
            return JsonResponse({'status': 'error', 'message': 'Permission refusée'}, status=403)
            
        rdv.status = 'confirmed'
        rdv.save()
        
        if request.headers.get('x-requested-with') == 'XMLHttpRequest' or request.content_type == 'application/json':
            return JsonResponse({'status': 'success', 'new_status': 'confirmed', 'message': f'Rendez-vous de {rdv.patient.username} accepté avec succès !'})
            
        messages.success(request, f"✅ Le rendez-vous de {rdv.patient.username} ({rdv.date.strftime('%d/%m/%Y')} à {rdv.time_slot}) a été accepté avec succès !")
        return redirect('medecins:dashboard')


class RejectAppointmentView(LoginRequiredMixin, View):
    def post(self, request, pk, *args, **kwargs):
        rdv = get_object_or_404(RendezVous, pk=pk)
        if request.user != rdv.doctor and not request.user.is_superuser:
            return JsonResponse({'status': 'error', 'message': 'Permission refusée'}, status=403)
            
        rdv.status = 'cancelled'
        rdv.in_waiting_room = False
        rdv.save()
        
        if request.headers.get('x-requested-with') == 'XMLHttpRequest' or request.content_type == 'application/json':
            return JsonResponse({'status': 'success', 'new_status': 'cancelled', 'message': f'Rendez-vous de {rdv.patient.username} refusé.'})
            
        messages.warning(request, f"⚠️ Le rendez-vous de {rdv.patient.username} ({rdv.date.strftime('%d/%m/%Y')} à {rdv.time_slot}) a été refusé / annulé.")
        return redirect('medecins:dashboard')
