from django.shortcuts import render, redirect, get_object_or_404
from django.views.generic import TemplateView, ListView, UpdateView, View, DetailView
from django.contrib.auth.mixins import UserPassesTestMixin
from django.contrib import messages
from django.urls import reverse_lazy
from django.db.models import Count, Sum
from django.utils import timezone
from datetime import timedelta

# Models
from accounts.models import CustomUser
from medecins.models import DoctorProfile
from pharmacies.models import PharmacyProfile
from consultations.models import RendezVous
from ordonnances.models import Ordonnance
from .models import SiteAppearance, Report, StaticPage, ActivityLog

class AdminRequiredMixin(UserPassesTestMixin):
    def test_func(self):
        return self.request.user.is_authenticated and self.request.user.role == 'admin'

    def handle_no_permission(self):
        messages.error(self.request, "Accès refusé. Vous devez être administrateur.")
        return redirect('core:home')

def log_action(user, action, action_type='autre', content_object=None, ip_address=None):
    ActivityLog.objects.create(
        user=user if user.is_authenticated else None,
        action=action,
        action_type=action_type,
        content_object=content_object,
        ip_address=ip_address
    )

class DashboardView(AdminRequiredMixin, TemplateView):
    template_name = 'administration/dashboard.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        thirty_days_ago = timezone.now() - timedelta(days=30)
        
        context['total_patients'] = CustomUser.objects.filter(role=CustomUser.PATIENT).count()
        context['total_doctors'] = CustomUser.objects.filter(role=CustomUser.MEDECIN).count()
        context['pending_doctors'] = DoctorProfile.objects.filter(verification_status=DoctorProfile.STATUS_PENDING).count()
        context['total_pharmacies'] = CustomUser.objects.filter(role=CustomUser.PHARMACIE).count()
        context['pending_pharmacies'] = PharmacyProfile.objects.filter(verification_status=PharmacyProfile.STATUS_PENDING).count()
        context['total_consultations'] = RendezVous.objects.count()
        context['recent_consultations'] = RendezVous.objects.filter(created_at__gte=thirty_days_ago).count() if hasattr(RendezVous, 'created_at') else 0
        context['total_ordonnances'] = Ordonnance.objects.count()
        
        context['recent_users'] = CustomUser.objects.all().order_by('-date_joined')[:5]
        
        # Graph Data (7 last days)
        from django.db.models import Count
        from django.db.models.functions import TruncDate
        import json
        
        seven_days_ago = timezone.now() - timedelta(days=7)
        consults_by_day = RendezVous.objects.filter(
            created_at__gte=seven_days_ago
        ).annotate(day=TruncDate('created_at')).values('day').annotate(count=Count('id')).order_by('day')
        
        labels = []
        data = []
        today = timezone.now().date()
        for i in range(6, -1, -1):
            date_i = today - timedelta(days=i)
            labels.append(date_i.strftime('%d/%m'))
            count = next((item['count'] for item in consults_by_day if item['day'] == date_i), 0)
            data.append(count)
            
        context['chart_labels'] = json.dumps(labels)
        context['chart_data'] = json.dumps(data)
        
        return context

class UserListView(AdminRequiredMixin, ListView):
    model = CustomUser
    template_name = 'administration/users_list.html'
    context_object_name = 'users'
    paginate_by = 20

    def get_queryset(self):
        qs = CustomUser.objects.all().order_by('-date_joined')
        role = self.request.GET.get('role')
        search = self.request.GET.get('search')
        if role:
            qs = qs.filter(role=role)
        if search:
            qs = qs.filter(username__icontains=search) | qs.filter(email__icontains=search)
        return qs

import csv
from django.http import HttpResponse

class UserExportCSVView(AdminRequiredMixin, View):
    def get(self, request, *args, **kwargs):
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = 'attachment; filename="utilisateurs.csv"'
        
        writer = csv.writer(response)
        writer.writerow(['ID', 'Nom d\'utilisateur', 'Email', 'Rôle', 'Statut', 'Date d\'inscription'])
        
        qs = CustomUser.objects.all().order_by('-date_joined')
        role = request.GET.get('role')
        search = request.GET.get('search')
        
        if role:
            qs = qs.filter(role=role)
        if search:
            qs = qs.filter(username__icontains=search) | qs.filter(email__icontains=search)
            
        for user in qs:
            status = 'Actif' if user.is_active else 'Inactif'
            writer.writerow([user.id, user.username, user.email, user.get_role_display(), status, user.date_joined.strftime('%Y-%m-%d %H:%M:%S')])
            
        log_action(request.user, "Export CSV des utilisateurs", action_type='admin')
        return response

class UserToggleStatusView(AdminRequiredMixin, View):
    def post(self, request, pk, *args, **kwargs):
        user = get_object_or_404(CustomUser, pk=pk)
        if user == request.user:
            messages.error(request, "Vous ne pouvez pas suspendre votre propre compte.")
            return redirect(request.META.get('HTTP_REFERER', 'administration:users_list'))
        
        user.is_active = not user.is_active
        user.save()
        
        status = "réactivé" if user.is_active else "suspendu"
        messages.success(request, f"Le compte de {user.username} a été {status}.")
        log_action(request.user, f"Compte {status}", action_type='admin', content_object=user)
        
        return redirect(request.META.get('HTTP_REFERER', 'administration:users_list'))

class UserResetPasswordView(AdminRequiredMixin, View):
    def post(self, request, pk, *args, **kwargs):
        from django.contrib.auth.forms import PasswordResetForm
        from django.conf import settings
        user = get_object_or_404(CustomUser, pk=pk)
        form = PasswordResetForm({'email': user.email})
        if form.is_valid():
            form.save(
                request=request,
                use_https=request.is_secure(),
                from_email=getattr(settings, 'DEFAULT_FROM_EMAIL', 'noreply@fransick.com'),
                email_template_name='registration/password_reset_email.html'
            )
            messages.success(request, f"Un email de réinitialisation a été envoyé à {user.email}.")
            log_action(request.user, "Envoi lien de réinitialisation MDP", action_type='admin', content_object=user)
        else:
            messages.error(request, "Impossible d'envoyer l'email de réinitialisation.")
        return redirect(request.META.get('HTTP_REFERER', 'administration:users_list'))

class UserDeactivateView(AdminRequiredMixin, View):
    def post(self, request, pk, *args, **kwargs):
        user = get_object_or_404(CustomUser, pk=pk)
        if user == request.user:
            messages.error(request, "Vous ne pouvez pas désactiver votre propre compte.")
        else:
            user.is_active = False
            user.save()
            messages.success(request, f"Le compte de {user.username} a été désactivé.")
            log_action(request.user, "Désactivation du compte", action_type='admin', content_object=user)
        return redirect(request.META.get('HTTP_REFERER', 'administration:users_list'))

class UserArchiveView(AdminRequiredMixin, View):
    def post(self, request, pk, *args, **kwargs):
        user = get_object_or_404(CustomUser, pk=pk)
        if user == request.user:
            messages.error(request, "Vous ne pouvez pas archiver votre propre compte.")
        else:
            user.is_active = False
            user.save()
            messages.success(request, f"L'utilisateur {user.username} a été archivé.")
            log_action(request.user, "Archivage utilisateur", action_type='admin', content_object=user)
        return redirect('administration:users_list')

class DoctorRequestsView(AdminRequiredMixin, ListView):
    model = DoctorProfile
    template_name = 'administration/requests_doctors.html'
    context_object_name = 'requests'

    def get_queryset(self):
        return DoctorProfile.objects.filter(verification_status=DoctorProfile.STATUS_PENDING).order_by('-submitted_at')

class DoctorApproveView(AdminRequiredMixin, View):
    def post(self, request, pk, *args, **kwargs):
        profile = get_object_or_404(DoctorProfile, pk=pk)
        profile.verification_status = DoctorProfile.STATUS_VERIFIED
        profile.verified_at = timezone.now()
        profile.save()
        messages.success(request, f"Le médecin {profile.user.username} a été approuvé.")
        log_action(request.user, "Validation médecin", action_type='admin', content_object=profile.user)
        return redirect('administration:doctor_requests')

class DoctorRejectView(AdminRequiredMixin, View):
    def post(self, request, pk, *args, **kwargs):
        profile = get_object_or_404(DoctorProfile, pk=pk)
        reason = request.POST.get('rejection_reason', '')
        profile.verification_status = DoctorProfile.STATUS_REJECTED
        profile.rejection_reason = reason
        profile.verified_at = timezone.now()
        profile.save()
        messages.success(request, f"Le médecin {profile.user.username} a été refusé.")
        log_action(request.user, "Refus médecin", action_type='admin', content_object=profile.user)
        return redirect('administration:doctor_requests')

class PharmacyRequestsView(AdminRequiredMixin, ListView):
    model = PharmacyProfile
    template_name = 'administration/requests_pharmacies.html'
    context_object_name = 'requests'

    def get_queryset(self):
        return PharmacyProfile.objects.filter(verification_status=PharmacyProfile.STATUS_PENDING).order_by('-submitted_at')

class PharmacyApproveView(AdminRequiredMixin, View):
    def post(self, request, pk, *args, **kwargs):
        profile = get_object_or_404(PharmacyProfile, pk=pk)
        profile.verification_status = PharmacyProfile.STATUS_VERIFIED
        profile.verified_at = timezone.now()
        profile.save()
        messages.success(request, f"La pharmacie {profile.pharmacy_name} a été approuvée.")
        log_action(request.user, "Validation pharmacie", action_type='admin', content_object=profile.user)
        return redirect('administration:pharmacy_requests')

class PharmacyRejectView(AdminRequiredMixin, View):
    def post(self, request, pk, *args, **kwargs):
        profile = get_object_or_404(PharmacyProfile, pk=pk)
        reason = request.POST.get('rejection_reason', '')
        profile.verification_status = PharmacyProfile.STATUS_REJECTED
        profile.rejection_reason = reason
        profile.verified_at = timezone.now()
        profile.save()
        messages.success(request, f"La pharmacie {profile.pharmacy_name} a été refusée.")
        log_action(request.user, "Refus pharmacie", action_type='admin', content_object=profile.user)
        return redirect('administration:pharmacy_requests')

class AnalyticsView(AdminRequiredMixin, TemplateView):
    template_name = 'administration/analytics.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        import json
        from django.db.models import Count
        from django.db.models.functions import TruncMonth, TruncDate
        
        # Inscriptions par mois (6 derniers mois)
        six_months_ago = timezone.now() - timedelta(days=180)
        users_by_month = CustomUser.objects.filter(date_joined__gte=six_months_ago).annotate(month=TruncMonth('date_joined')).values('month').annotate(count=Count('id')).order_by('month')
        
        month_labels = []
        user_counts = []
        for item in users_by_month:
            if item['month']:
                month_labels.append(item['month'].strftime('%B %Y'))
                user_counts.append(item['count'])
                
        context['users_chart_labels'] = json.dumps(month_labels)
        context['users_chart_data'] = json.dumps(user_counts)
        
        # Répartition des rôles
        role_counts = CustomUser.objects.values('role').annotate(count=Count('id'))
        roles = []
        counts = []
        for item in role_counts:
            roles.append(item['role'])
            counts.append(item['count'])
            
        context['roles_chart_labels'] = json.dumps(roles)
        context['roles_chart_data'] = json.dumps(counts)

        return context

class AppearanceView(AdminRequiredMixin, UpdateView):
    model = SiteAppearance
    template_name = 'administration/appearance.html'
    fields = [
        'app_name', 'hero_text', 'hero_description', 'hero_image', 
        'primary_color', 'secondary_color', 'logo', 'favicon',
        'facebook_url', 'twitter_url', 'instagram_url', 'linkedin_url',
        'contact_email', 'contact_phone', 'contact_address',
        'maintenance_mode', 'enable_ia_assistant', 'enable_payments'
    ]
    success_url = reverse_lazy('administration:appearance')

    def get_object(self, queryset=None):
        obj, created = SiteAppearance.objects.get_or_create(id=1)
        return obj

    def form_valid(self, form):
        messages.success(self.request, "Les paramètres d'apparence ont été mis à jour avec succès.")
        log_action(self.request.user, "Modification de l'apparence", action_type='admin', content_object=form.instance)
        return super().form_valid(form)

class ReportListView(AdminRequiredMixin, ListView):
    model = Report
    template_name = 'administration/report_list.html'
    context_object_name = 'reports'
    paginate_by = 20

class ReportDetailView(AdminRequiredMixin, UpdateView):
    model = Report
    template_name = 'administration/report_detail.html'
    fields = ['status', 'admin_response']
    success_url = reverse_lazy('administration:report_list')

    def form_valid(self, form):
        messages.success(self.request, "Le signalement a été mis à jour.")
        log_action(self.request.user, "Mise à jour d'un signalement", action_type='admin', content_object=self.object)
        return super().form_valid(form)

class StaticPageListView(AdminRequiredMixin, ListView):
    model = StaticPage
    template_name = 'administration/static_pages_list.html'
    context_object_name = 'pages'

class StaticPageEditView(AdminRequiredMixin, UpdateView):
    model = StaticPage
    template_name = 'administration/static_page_edit.html'
    fields = ['title', 'content']
    success_url = reverse_lazy('administration:static_pages')

    def form_valid(self, form):
        messages.success(self.request, "La page a été mise à jour.")
        log_action(self.request.user, f"Modification page statique {self.object.get_page_type_display()}", action_type='admin', content_object=self.object)
        return super().form_valid(form)

class ActivityLogView(AdminRequiredMixin, ListView):
    model = ActivityLog
    template_name = 'administration/activity_logs.html'
    context_object_name = 'logs'
    paginate_by = 50

    def get_queryset(self):
        qs = ActivityLog.objects.all().select_related('user').order_by('-created_at')
        action_type = self.request.GET.get('action_type')
        role = self.request.GET.get('role')
        search = self.request.GET.get('search')

        if action_type:
            qs = qs.filter(action_type=action_type)
        if role:
            qs = qs.filter(user__role=role)
        if search:
            qs = qs.filter(user__username__icontains=search) | qs.filter(action__icontains=search)
            
        return qs

class UserDetailView(AdminRequiredMixin, DetailView):
    model = CustomUser
    template_name = 'administration/user_detail.html'
    context_object_name = 'target_user'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.get_object()
        
        if user.role == CustomUser.MEDECIN:
            context['doctor_profile'] = getattr(user, 'doctor_profile', None)
            context['consultations'] = RendezVous.objects.filter(doctor=user).order_by('-date', '-time_slot')
            context['ordonnances'] = Ordonnance.objects.filter(doctor=user).order_by('-created_at')
        elif user.role == CustomUser.PATIENT:
            context['consultations'] = RendezVous.objects.filter(patient=user).order_by('-date', '-time_slot')
            context['ordonnances'] = Ordonnance.objects.filter(patient=user).order_by('-created_at')
        elif user.role == CustomUser.PHARMACIE:
            context['pharmacy_profile'] = getattr(user, 'pharmacy_profile', None)
            
        context['activity_logs'] = ActivityLog.objects.filter(user=user).order_by('-created_at')[:50]
        context['reports_received'] = Report.objects.filter(target_user=user).order_by('-created_at')
        context['reports_created'] = Report.objects.filter(author=user).order_by('-created_at')
        
        return context

class AdminSettingsView(AdminRequiredMixin, UpdateView):
    model = CustomUser
    template_name = 'administration/settings.html'
    fields = ['first_name', 'last_name', 'email', 'phone_number', 'profile_picture']
    success_url = reverse_lazy('administration:settings')

    def get_object(self, queryset=None):
        return self.request.user

    def form_valid(self, form):
        messages.success(self.request, "Vos paramètres ont été mis à jour.")
        return super().form_valid(form)

from django.contrib.auth.views import PasswordChangeView
class AdminPasswordChangeView(AdminRequiredMixin, PasswordChangeView):
    template_name = 'administration/password_change.html'
    success_url = reverse_lazy('administration:settings')

    def form_valid(self, form):
        messages.success(self.request, "Votre mot de passe a été modifié avec succès.")
        log_action(self.request.user, "Changement de mot de passe", action_type='admin')
        return super().form_valid(form)

from django.contrib.auth.models import Group

class AdminManagementView(AdminRequiredMixin, ListView):
    model = CustomUser
    template_name = 'administration/admins_list.html'
    context_object_name = 'admins'

    def get_queryset(self):
        return CustomUser.objects.filter(role='admin').order_by('-date_joined')
        
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # Create default groups if they don't exist
        for g in ['SuperAdmin', 'Modérateur', 'Valideur']:
            Group.objects.get_or_create(name=g)
        context['groups'] = Group.objects.all()
        return context

class AdminAssignGroupView(AdminRequiredMixin, View):
    def post(self, request, pk, *args, **kwargs):
        admin_user = get_object_or_404(CustomUser, pk=pk, role='admin')
        if admin_user == request.user:
            messages.error(request, "Vous ne pouvez pas modifier vos propres permissions.")
            return redirect('administration:admins_list')
            
        group_id = request.POST.get('group_id')
        admin_user.groups.clear()
        
        if group_id:
            group = get_object_or_404(Group, pk=group_id)
            admin_user.groups.add(group)
            messages.success(request, f"Le rôle de {admin_user.username} a été mis à jour ({group.name}).")
            log_action(request.user, f"Assignation du rôle {group.name} à {admin_user.username}", action_type='admin')
        else:
            messages.success(request, f"Les rôles de {admin_user.username} ont été révoqués.")
            log_action(request.user, f"Révocation des rôles de {admin_user.username}", action_type='admin')
            
        return redirect('administration:admins_list')
