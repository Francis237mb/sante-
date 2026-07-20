from django.views.generic import TemplateView

class ChatView(TemplateView):
    template_name = 'ia_assistant/chat.html'
