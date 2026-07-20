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

User = get_user_model()

class DashboardView(LoginRequiredMixin, TemplateView):
    template_name = 'patients/dashboard.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['medecins_list'] = User.objects.filter(role='medecin')
        context['videos_list'] = HealthVideo.objects.all()
        return context

class PatientSuiviView(LoginRequiredMixin, TemplateView):
    template_name = 'patients/suivi.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['medecins_list'] = User.objects.filter(role='medecin')
        context['videos_list'] = HealthVideo.objects.all()
        # Vrais rendez-vous du patient en BDD SQLite
        context['user_rdv_list'] = RendezVous.objects.filter(patient=self.request.user)
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
        context['profile'] = getattr(doctor, 'doctor_profile', None)
        context['subscribers_count'] = DoctorSubscription.objects.filter(doctor=doctor).count()
        context['is_subscribed'] = DoctorSubscription.objects.filter(patient=self.request.user, doctor=doctor).exists()
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
                status='confirmed'
            )
            messages.success(request, f"Votre rendez-vous du {date} à {time_slot} avec le Dr. {doctor.username} a été enregistré avec succès !")
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

        if 'update_profile' in request.POST:
            profile_form = PatientProfileForm(request.POST, request.FILES, instance=request.user)
            if profile_form.is_valid():
                profile_form.save()
                messages.success(request, "Vos informations personnelles ont été mises à jour avec succès.")
                return redirect('patients:settings')
            else:
                messages.error(request, "Veuillez corriger les erreurs ci-dessous.")
                active_tab = 'profile'

        elif 'change_password' in request.POST:
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
