from django.views.generic import TemplateView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import redirect
from django.contrib import messages
from .models import HealthVideo

class DashboardView(LoginRequiredMixin, TemplateView):
    template_name = 'medecins/dashboard.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        if self.request.user.is_authenticated:
            context['my_videos'] = HealthVideo.objects.filter(author=self.request.user)
        return context

    def post(self, request, *args, **kwargs):
        title = request.POST.get('title')
        description = request.POST.get('description')
        video_file = request.FILES.get('video_file')

        if title:
            HealthVideo.objects.create(
                author=request.user,
                title=title,
                description=description,
                video_file=video_file
            )
            messages.success(request, f"Votre capsule vidéo '{title}' a été publiée avec succès pour tous les patients !")
        else:
            messages.error(request, "Veuillez saisir un titre pour votre capsule vidéo.")
        
        return redirect('medecins:dashboard')
