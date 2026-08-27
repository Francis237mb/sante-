from django.views.generic import TemplateView, View
from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import redirect, get_object_or_404, render
from django.http import JsonResponse
from django.contrib import messages
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import ensure_csrf_cookie, csrf_protect
from django.contrib.auth.forms import PasswordChangeForm
from django.contrib.auth import update_session_auth_hash
from .models import HealthVideo, VideoComment, DoctorProfile, DoctorSubscription
from .forms import DoctorProfileForm
from ordonnances.models import Ordonnance
from consultations.models import RendezVous


@method_decorator(ensure_csrf_cookie, name='dispatch')
@method_decorator(csrf_protect, name='dispatch')
class DashboardView(LoginRequiredMixin, TemplateView):
    template_name = 'medecins/dashboard.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        if self.request.user.is_authenticated:
            if getattr(self.request.user, 'role', '') == 'medecin':
                if not hasattr(self.request.user, 'doctor_profile') or self.request.user.doctor_profile is None:
                    DoctorProfile.objects.get_or_create(
                        user=self.request.user,
                        defaults={
                            'speciality': 'Médecin Généraliste',
                            'clinic_address': 'Douala, Cameroun',
                            'about': 'Médecin praticien certifié inscrit sur la plateforme Fransick Santé.',
                            'is_verified': True,
                            'verification_status': 'verified',
                        }
                    )

            my_videos = HealthVideo.objects.filter(author=self.request.user).prefetch_related('comments')
            context['my_videos'] = my_videos
            context['my_videos_count'] = my_videos.count()
            
            # Vrais rendez-vous du médecin en BDD
            my_rdvs = RendezVous.objects.filter(doctor=self.request.user).select_related('patient').order_by('-date')
            context['my_rdvs'] = my_rdvs
            context['rdvs_count'] = my_rdvs.count()
            context['waiting_room_count'] = my_rdvs.filter(in_waiting_room=True).count()
            
            # Abonnés du médecin en BDD
            context['subscribers_count'] = DoctorSubscription.objects.filter(doctor=self.request.user).count()
            
            # Récupérer l'historique des ordonnances et diagnostics délivrés par ce médecin
            ordonnances = Ordonnance.objects.filter(doctor=self.request.user).select_related('patient').order_by('-date')
            context['my_ordonnances'] = ordonnances
            context['total_ordonnances_count'] = ordonnances.count()
            
            # Structurer les dossiers patients avec leurs derniers diagnostics
            patients_dict = {}
            for ord in ordonnances:
                p = ord.patient
                if p.id not in patients_dict:
                    patients_dict[p.id] = {
                        'patient': p,
                        'last_ordonnance': ord,
                        'all_ordonnances': [ord],
                        'diagnostic': ord.diagnostic,
                        'patient_age': ord.patient_age
                    }
                else:
                    patients_dict[p.id]['all_ordonnances'].append(ord)
                    
            my_patients_list = list(patients_dict.values())
            context['my_patients'] = my_patients_list
            context['my_patients_count'] = len(my_patients_list)

        return context


    def post(self, request, *args, **kwargs):
        title = request.POST.get('title')
        description = request.POST.get('description')
        video_file = request.FILES.get('video_file')

        if title:
            video = HealthVideo.objects.create(
                author=request.user,
                title=title,
                description=description,
                video_file=video_file if video_file else 'videos/sto_1.mp4'
            )
            messages.success(request, f"🎉 Votre capsule vidéo '{title}' a été publiée avec succès pour tous les patients !")
        else:
            messages.error(request, "Veuillez saisir un titre pour votre capsule vidéo.")
        
        return redirect('medecins:dashboard')


class DoctorPatientsListView(LoginRequiredMixin, TemplateView):
    template_name = 'medecins/patients_list.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        ordonnances = Ordonnance.objects.filter(doctor=self.request.user).select_related('patient').order_by('-date')
        
        patients_dict = {}
        for ord in ordonnances:
            p = ord.patient
            if p.id not in patients_dict:
                patients_dict[p.id] = {
                    'patient': p,
                    'last_ordonnance': ord,
                    'all_ordonnances': [ord],
                    'diagnostic': ord.diagnostic,
                    'patient_age': ord.patient_age
                }
            else:
                patients_dict[p.id]['all_ordonnances'].append(ord)
                
        context['my_patients'] = list(patients_dict.values())
        context['total_ordonnances_count'] = ordonnances.count()
        return context


class AddVideoCommentView(LoginRequiredMixin, View):
    def post(self, request, pk, *args, **kwargs):
        video = get_object_or_404(HealthVideo, pk=pk)
        text = request.POST.get('text', '').strip()
        
        if not text:
            return JsonResponse({'status': 'error', 'message': 'Le commentaire ne peut pas être vide.'}, status=400)
            
        comment = VideoComment.objects.create(
            video=video,
            author=request.user,
            text=text
        )
        
        return JsonResponse({
            'status': 'success',
            'comment': {
                'id': comment.id,
                'author': comment.author.username,
                'text': comment.text,
                'created_at': comment.created_at.strftime('%d/%m/%Y à %H:%M')
            },
            'total_comments': video.comments.count()
        })


class DeleteVideoView(LoginRequiredMixin, View):
    def post(self, request, pk, *args, **kwargs):
        video = get_object_or_404(HealthVideo, pk=pk, author=request.user)
        title = video.title
        video.delete()
        messages.success(request, f"La capsule vidéo '{title}' a été supprimée.")
        return redirect('medecins:dashboard')


class DoctorSettingsView(LoginRequiredMixin, TemplateView):
    template_name = 'medecins/settings.html'

    def get(self, request, *args, **kwargs):
        profile_form = DoctorProfileForm(instance=request.user)
        password_form = PasswordChangeForm(user=request.user)
        context = {
            'profile_form': profile_form,
            'password_form': password_form,
            'active_tab': 'profile'
        }
        return render(request, self.template_name, context)

    def post(self, request, *args, **kwargs):
        active_tab = request.POST.get('active_tab', 'profile')
        profile_form = DoctorProfileForm(instance=request.user)
        password_form = PasswordChangeForm(user=request.user)
        action = request.POST.get('action')

        if 'update_profile' in request.POST or action == 'update_profile':
            profile_form = DoctorProfileForm(request.POST, request.FILES, instance=request.user)
            if profile_form.is_valid():
                profile_form.save()
                messages.success(request, "Les paramètres et informations de votre cabinet ont été mis à jour avec succès.")
                return redirect('medecins:settings')
            else:
                messages.error(request, "Veuillez corriger les erreurs indiquées dans le formulaire.")
                active_tab = 'profile'

        elif 'change_password' in request.POST or action == 'change_password':
            password_form = PasswordChangeForm(user=request.user, data=request.POST)
            if password_form.is_valid():
                user = password_form.save()
                update_session_auth_hash(request, user)
                messages.success(request, "Votre mot de passe a été modifié avec succès.")
                return redirect('medecins:settings')
            else:
                messages.error(request, "Veuillez corriger les erreurs de mot de passe ci-dessous.")
                active_tab = 'password'

        context = {
            'profile_form': profile_form,
            'password_form': password_form,
            'active_tab': active_tab
        }
        return render(request, self.template_name, context)

