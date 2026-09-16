from django.views.generic import TemplateView
from django.shortcuts import redirect
from django.urls import reverse_lazy
from django.contrib.auth.views import LogoutView as DjangoLogoutView
from django.contrib.auth.views import LoginView as DjangoLoginView
from django.contrib.auth import login as auth_login
from django.views.generic.edit import CreateView
from django.contrib import messages

from django.utils.decorators import method_decorator
from .forms import CustomUserCreationForm

def get_dashboard_url_for_user(user):
    if not user or not user.is_authenticated:
        return 'core:home'
    role = getattr(user, 'role', None)
    if role == 'admin' or getattr(user, 'is_superuser', False) or getattr(user, 'is_staff', False):
        return 'administration:dashboard'
    if role == 'patient':
        return 'patients:dashboard'
    elif role == 'medecin':
        return 'medecins:dashboard'
    elif role == 'pharmacie':
        return 'pharmacies:list'
    return 'core:home'

class LoginPatientView(DjangoLoginView):
    template_name = 'accounts/login_patient.html'
    redirect_authenticated_user = True

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['role_title'] = "Patient"
        return context

    def get_success_url(self):
        return reverse_lazy(get_dashboard_url_for_user(self.request.user))

    def form_valid(self, form):
        auth_login(self.request, form.get_user())
        user = self.request.user
        if user.role != 'patient':
            messages.info(self.request, f"Vous êtes connecté en tant que {user.get_role_display()}.")
        return redirect(get_dashboard_url_for_user(user))

class LoginMedecinView(DjangoLoginView):
    template_name = 'accounts/login_medecin.html'
    redirect_authenticated_user = True

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['role_title'] = "Médecin"
        return context

    def get_success_url(self):
        return reverse_lazy(get_dashboard_url_for_user(self.request.user))

    def form_valid(self, form):
        user = form.get_user()
        if user.role == 'medecin':
            profile = getattr(user, 'doctor_profile', None)
            if profile and not getattr(profile, 'is_verified', True):
                status = getattr(profile, 'verification_status', 'pending')
                if status == 'rejected':
                    reason = getattr(profile, 'rejection_reason', '') or "Votre candidature n'a pas été retenue par notre équipe."
                    messages.error(self.request, f"❌ Votre demande d'inscription médecin a été refusée. Motif : {reason}")
                else:
                    messages.warning(self.request, "⏳ Votre compte médecin est actuellement en attente de validation par notre équipe administrative. Vous recevrez une notification dès que votre accès sera autorisé.")
                return redirect('accounts:login_medecin')

        auth_login(self.request, user)
        if user.role != 'medecin':
            messages.info(self.request, f"Vous êtes connecté en tant que {user.get_role_display()}.")
        return redirect(get_dashboard_url_for_user(user))

class LoginPharmacieView(DjangoLoginView):
    template_name = 'accounts/login_pharmacie.html'
    redirect_authenticated_user = True

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['role_title'] = "Pharmacie"
        return context

    def get_success_url(self):
        return reverse_lazy(get_dashboard_url_for_user(self.request.user))

    def form_valid(self, form):
        auth_login(self.request, form.get_user())
        user = self.request.user
        if user.role != 'pharmacie':
            messages.info(self.request, f"Vous êtes connecté en tant que {user.get_role_display()}.")
        return redirect(get_dashboard_url_for_user(user))

class LogoutView(DjangoLogoutView):
    next_page = 'core:home'

class RegisterView(CreateView):
    template_name = 'accounts/register.html'
    form_class = CustomUserCreationForm

    def dispatch(self, request, *args, **kwargs):
        if request.user.is_authenticated:
            return redirect(get_dashboard_url_for_user(request.user))
        return super().dispatch(request, *args, **kwargs)

    def form_valid(self, form):
        user = form.save()
        if user.role == 'medecin':
            messages.success(
                self.request,
                "🩺 Votre demande d'inscription a été envoyée. Vous recevrez une notification une fois votre compte validé par notre équipe administrative avant de pouvoir vous identifier."
            )
            return redirect('accounts:login_medecin')
        elif user.role == 'pharmacie':
            # Auto-login for pharmacie as well, unless they need verification
            auth_login(self.request, user)
            messages.success(
                self.request,
                "Votre compte a été créé avec succès. Bienvenue dans votre espace Pharmacie."
            )
            return redirect(get_dashboard_url_for_user(user))
        
        # Auto-login for patients
        auth_login(self.request, user)
        messages.success(
            self.request, 
            "Votre compte a été créé avec succès. Bienvenue !"
        )
        return redirect(get_dashboard_url_for_user(user))
