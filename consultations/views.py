from django.views.generic import TemplateView

class ConsultationListView(TemplateView):
    template_name = 'consultations/list.html'
