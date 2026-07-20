from django.views.generic import TemplateView

class PharmacyListView(TemplateView):
    template_name = 'pharmacies/list.html'
