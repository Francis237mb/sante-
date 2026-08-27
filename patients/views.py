from django.views.generic import TemplateView, DetailView, View
from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse
from django.contrib import messages
from django.contrib.auth import update_session_auth_hash, get_user_model
from django.contrib.auth.forms import PasswordChangeForm
from .forms import PatientProfileForm
from medecins.models import HealthVideo, DoctorProfile, DoctorSubscription
from consultations.models import RendezVous
from ordonnances.models import Ordonnance
from pharmacies.models import PharmacyProfile, Medicament

User = get_user_model()

def get_all_registered_medecins():
    """
    Récupère tous les médecins inscrits en base de données réelle et s'assure qu'un profil existe pour chacun.
    """
    medecins = User.objects.filter(role='medecin').order_by('id')
    for doc in medecins:
        if not hasattr(doc, 'doctor_profile') or doc.doctor_profile is None:
            DoctorProfile.objects.get_or_create(
                user=doc,
                defaults={
                    'speciality': 'Médecin Généraliste',
                    'clinic_address': 'Douala, Cameroun',
                    'about': 'Médecin praticien certifié inscrit sur la plateforme Fransick Santé.'
                }
            )
    return User.objects.filter(role='medecin').order_by('id')

class DashboardView(LoginRequiredMixin, TemplateView):
    template_name = 'patients/dashboard.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['medecins_list'] = get_all_registered_medecins()
        context['videos_list'] = HealthVideo.objects.all().order_by('-created_at')
        # Pharmacies et Médicaments pour la recherche globale
        context['pharmacies_list'] = User.objects.filter(role='pharmacie')
        context['medicaments_list'] = Medicament.objects.all()
        return context

class PatientSuiviView(LoginRequiredMixin, TemplateView):
    template_name = 'patients/suivi.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['medecins_list'] = get_all_registered_medecins()
        context['videos_list'] = HealthVideo.objects.all()
        context['pharmacies_list'] = User.objects.filter(role='pharmacie')
        context['medicaments_list'] = Medicament.objects.all()
        # Vrais rendez-vous & ordonnances du patient en BDD SQLite
        context['user_rdv_list'] = RendezVous.objects.filter(patient=self.request.user)
        context['user_ordonnances_list'] = Ordonnance.objects.filter(patient=self.request.user)
        return context

class DoctorDetailView(LoginRequiredMixin, DetailView):
    model = User
    template_name = 'patients/doctor_detail.html'
    context_object_name = 'doctor'

    def get_queryset(self):
        return User.objects.filter(role='medecin')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        doctor = self.get_object()
        if not hasattr(doctor, 'doctor_profile') or doctor.doctor_profile is None:
            DoctorProfile.objects.get_or_create(
                user=doctor,
                defaults={
                    'speciality': 'Médecin Généraliste',
                    'clinic_address': 'Douala, Cameroun',
                    'about': 'Médecin praticien certifié inscrit sur la plateforme Fransick Santé.'
                }
            )
        context['profile'] = getattr(doctor, 'doctor_profile', None)
        context['subscribers_count'] = DoctorSubscription.objects.filter(doctor=doctor).count()
        context['is_subscribed'] = DoctorSubscription.objects.filter(patient=self.request.user, doctor=doctor).exists()
        context['pharmacies_list'] = User.objects.filter(role='pharmacie')
        context['medicaments_list'] = Medicament.objects.all()
        context['medecins_list'] = get_all_registered_medecins()
        return context



class BookAppointmentView(LoginRequiredMixin, View):
    def post(self, request, pk, *args, **kwargs):
        doctor = get_object_or_404(User, pk=pk, role='medecin')
        consultation_type = request.POST.get('consultation_type', 'video')
        date = request.POST.get('date')
        time_slot = request.POST.get('time_slot', '10:00')
        reason = request.POST.get('reason', 'Consultation médicale')
        notes = request.POST.get('notes', '')

        if date:
            rdv = RendezVous.objects.create(
                patient=request.user,
                doctor=doctor,
                consultation_type=consultation_type,
                date=date,
                time_slot=time_slot,
                reason=reason,
                notes=notes,
                status='pending'
            )
            messages.success(request, f"⏳ Votre demande de rendez-vous du {date} à {time_slot} a été envoyée au Dr. {doctor.username} pour confirmation.")
            return redirect('patients:suivi')
        else:
            messages.error(request, "Veuillez sélectionner une date valide pour votre rendez-vous.")
            return redirect('patients:doctor_detail', pk=doctor.pk)

class DoctorSubscribeToggleView(LoginRequiredMixin, View):
    def post(self, request, pk, *args, **kwargs):
        doctor = get_object_or_404(User, pk=pk, role='medecin')
        subscription, created = DoctorSubscription.objects.get_or_create(patient=request.user, doctor=doctor)
        
        if not created:
            subscription.delete()
            is_subscribed = False
            status_str = 'unsubscribed'
        else:
            is_subscribed = True
            status_str = 'subscribed'

        count = DoctorSubscription.objects.filter(doctor=doctor).count()
        return JsonResponse({
            'status': status_str,
            'is_subscribed': is_subscribed,
            'count': count
        })

class PatientSettingsView(LoginRequiredMixin, TemplateView):
    template_name = 'patients/settings.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['pharmacies_list'] = User.objects.filter(role='pharmacie')
        return context

    def get(self, request, *args, **kwargs):
        profile_form = PatientProfileForm(instance=request.user)
        password_form = PasswordChangeForm(user=request.user)
        context = self.get_context_data(
            profile_form=profile_form,
            password_form=password_form,
            active_tab='profile'
        )
        return render(request, self.template_name, context)

    def post(self, request, *args, **kwargs):
        active_tab = request.POST.get('active_tab', 'profile')
        profile_form = PatientProfileForm(instance=request.user)
        password_form = PasswordChangeForm(user=request.user)

        action = request.POST.get('action')

        if 'update_profile' in request.POST or action == 'update_profile':
            profile_form = PatientProfileForm(request.POST, request.FILES, instance=request.user)
            if profile_form.is_valid():
                profile_form.save()
                messages.success(request, "Vos informations personnelles ont été mises à jour avec succès.")
                return redirect('patients:settings')
            else:
                messages.error(request, "Veuillez corriger les erreurs ci-dessous.")
                active_tab = 'profile'

        elif 'change_password' in request.POST or action == 'change_password':
            password_form = PasswordChangeForm(user=request.user, data=request.POST)
            if password_form.is_valid():
                user = password_form.save()
                update_session_auth_hash(request, user)
                messages.success(request, "Votre mot de passe a été modifié avec succès.")
                return redirect('patients:settings')
            else:
                messages.error(request, "Veuillez corriger les erreurs de mot de passe ci-dessous.")
                active_tab = 'password'

        context = self.get_context_data(
            profile_form=profile_form,
            password_form=password_form,
            active_tab=active_tab
        )
        return render(request, self.template_name, context)

class PharmacyListView(LoginRequiredMixin, TemplateView):
    template_name = 'patients/pharmacies.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['medecins_list'] = get_all_registered_medecins()
        context['videos_list'] = HealthVideo.objects.all()
        context['pharmacies_list'] = User.objects.filter(role='pharmacie')
        context['medicaments_list'] = Medicament.objects.all()
        return context


class PatientVideosFeedView(LoginRequiredMixin, TemplateView):
    template_name = 'patients/videos.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        videos = HealthVideo.objects.select_related('author', 'author__doctor_profile').prefetch_related('comments', 'comments__author').order_by('-created_at')
        followed_doctor_ids = set(DoctorSubscription.objects.filter(patient=self.request.user).values_list('doctor_id', flat=True))
        liked_video_ids = set(self.request.session.get('liked_videos', []))

        context['videos'] = videos
        context['followed_doctor_ids'] = followed_doctor_ids
        context['liked_video_ids'] = liked_video_ids
        context['medecins_list'] = get_all_registered_medecins()
        context['pharmacies_list'] = User.objects.filter(role='pharmacie')
        return context


class ToggleVideoLikeView(LoginRequiredMixin, View):
    def post(self, request, pk, *args, **kwargs):
        video = get_object_or_404(HealthVideo, pk=pk)
        session_likes = request.session.get('liked_videos', [])
        if pk in session_likes:
            video.likes_count = max(0, video.likes_count - 1)
            video.save()
            session_likes.remove(pk)
            liked = False
        else:
            video.likes_count += 1
            video.save()
            session_likes.append(pk)
            liked = True
            
        request.session['liked_videos'] = session_likes
        return JsonResponse({
            'status': 'success',
            'liked': liked,
            'likes_count': video.likes_count
        })


def api_live_medecins(request):
    """
    API en temps réel pour récupérer la liste actualisée de tous les médecins inscrits
    (ex: si un médecin s'est inscrit sur un autre appareil ou téléphone connecté au réseau).
    """
    medecins = get_all_registered_medecins()
    med_list = []
    for doc in medecins:
        profile = getattr(doc, 'doctor_profile', None)
        speciality = profile.speciality if (profile and profile.speciality) else "Spécialité non renseignée"
        rating = str(profile.rating) if (profile and profile.rating is not None) else "0.0"
        exp = profile.years_of_experience if (profile and profile.years_of_experience is not None) else 0
        
        if doc.first_name or doc.last_name:
            full_title_name = f"Dr. {doc.first_name} {doc.last_name}".strip()
            simple_name = f"{doc.first_name} {doc.last_name}".strip()
        else:
            full_title_name = f"Dr. {doc.username}"
            simple_name = doc.username
            
        med_list.append({
            'id': doc.id,
            'username': doc.username,
            'full_title_name': full_title_name,
            'simple_name': simple_name,
            'speciality': speciality,
            'speciality_lower': speciality.lower(),
            'rating': rating,
            'years_of_experience': exp,
            'profile_picture_url': doc.profile_picture.url if doc.profile_picture else "",
            'detail_url': f"/patients/medecin/{doc.id}/",
            'search_term': f"{doc.username} {simple_name}".lower()
        })
    
    return JsonResponse({
        'status': 'success',
        'count': len(med_list),
        'medecins': med_list
    })

