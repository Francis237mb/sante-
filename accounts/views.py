from django.views.generic import TemplateView
from django.shortcuts import redirect
from django.urls import reverse_lazy
from django.contrib.auth.views import LogoutView as DjangoLogoutView
from django.contrib.auth.views import LoginView as DjangoLoginView
from django.contrib.auth import login as auth_login
from django.views.generic.edit import CreateView
from django.contrib import messages
from .forms import CustomUserCreationForm

def get_dashboard_url_for_user(user):
    if not user or not user.is_authenticated:
        return 'core:home'
    role = getattr(user, 'role', None)
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
        auth_login(self.request, form.get_user())
        user = self.request.user
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
        auth_login(self.request, user)
        return redirect(get_dashboard_url_for_user(user))
