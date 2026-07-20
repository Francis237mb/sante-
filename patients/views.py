from django.views.generic import TemplateView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import render, redirect
from django.contrib import messages
from django.contrib.auth import update_session_auth_hash, get_user_model
from django.contrib.auth.forms import PasswordChangeForm
from .forms import PatientProfileForm
from medecins.models import HealthVideo

User = get_user_model()

class DashboardView(LoginRequiredMixin, TemplateView):
    template_name = 'patients/dashboard.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # Récupération de tous les médecins inscrits sur la plateforme (dont Dr. Wada)
        context['medecins_list'] = User.objects.filter(role='medecin')
        # Récupération de toutes les vidéos publiées par les médecins
        context['videos_list'] = HealthVideo.objects.all()
        return context

class PatientSuiviView(LoginRequiredMixin, TemplateView):
    template_name = 'patients/suivi.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['medecins_list'] = User.objects.filter(role='medecin')
        context['videos_list'] = HealthVideo.objects.all()
        return context

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
        return self.render_to_response(context)

    def post(self, request, *args, **kwargs):
        action = request.POST.get('action')
        profile_form = PatientProfileForm(instance=request.user)
        password_form = PasswordChangeForm(user=request.user)

        if action == 'update_profile':
            profile_form = PatientProfileForm(request.POST, request.FILES, instance=request.user)
            if profile_form.is_valid():
                profile_form.save()
                messages.success(request, "Votre profil a été mis à jour avec succès.")
                return redirect('patients:settings')
            else:
                messages.error(request, "Une erreur est survenue lors de la mise à jour de votre profil.")

        elif action == 'change_password':
            password_form = PasswordChangeForm(user=request.user, data=request.POST)
            if password_form.is_valid():
                user = password_form.save()
                update_session_auth_hash(request, user)
                messages.success(request, "Votre mot de passe a été modifié avec succès.")
                return redirect('patients:settings')
            else:
                messages.error(request, "Veuillez corriger les erreurs de saisie du mot de passe.")

        context = self.get_context_data(
            profile_form=profile_form,
            password_form=password_form,
            active_tab='security' if action == 'change_password' else 'profile'
        )
        return self.render_to_response(context)
