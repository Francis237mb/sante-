from django.views.generic import TemplateView

class OrdonnanceListView(TemplateView):
    template_name = 'ordonnances/list.html'
