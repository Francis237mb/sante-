from django.views.generic import TemplateView, CreateView, ListView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.urls import reverse_lazy
from django.contrib import messages
from administration.models import Report
from administration.views import log_action

class HomeView(TemplateView):
    template_name = 'core/home.html'

class AboutView(TemplateView):
    template_name = 'core/about.html'

class CGUView(TemplateView):
    template_name = 'core/cgu.html'

class SubmitReportView(LoginRequiredMixin, CreateView):
    model = Report
    template_name = 'core/submit_report.html'
    fields = ['report_type', 'title', 'description', 'attachment']
    success_url = reverse_lazy('core:my_reports')

    def form_valid(self, form):
        form.instance.author = self.request.user
        messages.success(self.request, "Votre signalement a été envoyé avec succès.")
        response = super().form_valid(form)
        log_action(self.request.user, "Soumission d'un signalement", action_type='signalement', content_object=form.instance)
        return response

class MyReportsView(LoginRequiredMixin, ListView):
    model = Report
    template_name = 'core/my_reports.html'
    context_object_name = 'reports'

    def get_queryset(self):
        return Report.objects.filter(author=self.request.user).order_by('-created_at')
