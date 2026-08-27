import os
import json
import openai
from django.conf import settings
from django.views.generic import TemplateView, View
from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import JsonResponse, HttpResponseRedirect
from django.urls import reverse
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
import urllib.request
import urllib.parse
import urllib.error
from .models import ChatMessage, Conversation
from .medical_engine import analyze_and_generate_response

def get_ai_api_config():
    """
    Récupère la clé API (Groq ou OpenAI) depuis le fichier .env ou les variables d'environnement.
    Détecte automatiquement si c'est Groq (clé commençant par gsk_ ou variable GROQ_API_KEY).
    """
    api_key = ''
    provider = 'openai'

    try:
        env_file = settings.BASE_DIR / '.env'
        if env_file.exists():
            with open(env_file, 'r', encoding='utf-8') as f:
                for line in f:
                    line = line.strip()
                    if line.startswith('GROQ_API_KEY=') or line.startswith('OPENAI_API_KEY=') or line.startswith('AI_API_KEY='):
                        val = line.split('=', 1)[1].strip(' "\'')
                        if val:
                            if val.startswith('gsk_'):
                                return {'key': val, 'provider': 'groq'}
                            elif not api_key:
                                api_key = val
                                if line.startswith('GROQ_API_KEY='):
                                    provider = 'groq'
    except Exception as e:
        print("Erreur lecture .env :", e)

    # Fallback variables d'environnement & settings
    if not api_key:
        for k in ['GROQ_API_KEY', 'OPENAI_API_KEY', 'AI_API_KEY']:
            val = getattr(settings, k, '') or os.getenv(k, '')
            if val:
                api_key = val
                if k == 'GROQ_API_KEY' or val.startswith('gsk_'):
                    provider = 'groq'
                break

    if api_key and api_key.startswith('gsk_'):
        provider = 'groq'

    return {'key': api_key, 'provider': provider}

def call_ai_llm_service(api_config, messages_payload):
    """
    Appelle l'API Groq ou OpenAI en HTTP direct avec gestion automatique et rotation des modèles de pointe.
    """
    api_key = api_config.get('key')
    provider = api_config.get('provider')

    if not api_key:
        raise ValueError("Aucune clé API (Groq/OpenAI) trouvée.")

    if provider == 'groq':
        url = "https://api.groq.com/openai/v1/chat/completions"
        # Liste de repli automatique sur les modèles officiels performants de Groq
        models = ["llama-3.3-70b-versatile", "mixtral-8x7b-32768", "llama3-70b-8192", "llama-3.1-8b-instant", "gemma2-9b-it", "llama3-8b-8192"]
    else:
        url = "https://api.openai.com/v1/chat/completions"
        models = ["gpt-4o-mini", "gpt-4o", "gpt-3.5-turbo"]

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"
    }

    for model in models:
        try:
            payload = {
                "model": model,
                "messages": messages_payload,
                "temperature": 0.7,
                "max_tokens": 1500
            }
            req = urllib.request.Request(url, data=json.dumps(payload).encode('utf-8'), headers=headers)
            with urllib.request.urlopen(req, timeout=20) as resp:
                resp_data = json.loads(resp.read().decode('utf-8'))
                reply = resp_data['choices'][0]['message']['content'].strip()
                if reply:
                    return reply
        except Exception as e:
            print(f"Tentative modèle {model} ({provider}) en échec : {e}")
            continue

    raise RuntimeError(f"Échec de communication avec tous les modèles pour {provider}.")

def generate_medical_fallback_response(query):
    """
    Délégation au Moteur Médical Virtuel & NLP de Fransick Santé.
    Génère une réponse clinique approfondie, précise et variée à partir d'une analyse sémantique du message.
    """
    return analyze_and_generate_response(query)

class ChatView(LoginRequiredMixin, TemplateView):
    template_name = 'ia_assistant/chat.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user

        # 1. Rattraper les messages sans conversation (migration de l'ancien système)
        orphans = ChatMessage.objects.filter(user=user, conversation__isnull=True)
        if orphans.exists():
            default_conv = Conversation.objects.create(user=user, title="Consultation précédente")
            orphans.update(conversation=default_conv)

        # 2. Récupérer toutes les conversations propres à l'utilisateur
        conversations = Conversation.objects.filter(user=user).order_by('-updated_at')

        conversation_id = kwargs.get('conversation_id') or self.request.GET.get('c')
        active_conversation = None

        if conversation_id:
            active_conversation = conversations.filter(id=conversation_id).first()

        # Si aucune conversation spécifique sélectionnée (ou paramètre ?new=1), prendre la première ou rien
        if not active_conversation and not self.request.GET.get('new'):
            active_conversation = conversations.first()

        context['conversations'] = conversations
        context['active_conversation'] = active_conversation
        
        if active_conversation:
            context['chat_history'] = active_conversation.messages.all().order_by('timestamp')
        else:
            context['chat_history'] = []

        # Identifier si l'utilisateur est un médecin pour adapter l'UI et la barre de navigation
        context['is_doctor'] = (user.role == 'medecin' or getattr(user, 'doctor_profile', None) is not None)
        return context

@method_decorator(csrf_exempt, name='dispatch')
class AIChatApiView(LoginRequiredMixin, View):
    """
    Vue API AJAX pour communiquer avec l'Assistant IA alimenté par Groq (Llama-3/Mixtral) ou OpenAI.
    Gère des conversations propres à chaque utilisateur (médecin ou patient).
    """
    def post(self, request, *args, **kwargs):
        try:
            data = json.loads(request.body.decode('utf-8'))
            user_message = data.get('message', '').strip()
            conversation_id = data.get('conversation_id')
        except Exception:
            user_message = request.POST.get('message', '').strip()
            conversation_id = request.POST.get('conversation_id')

        if not user_message:
            return JsonResponse({'status': 'error', 'message': 'Veuillez saisir une question.'}, status=400)

        api_config = get_ai_api_config()
        user = request.user

        # 1. Gestion ou création de la conversation propre à l'utilisateur
        conversation = None
        if conversation_id:
            conversation = Conversation.objects.filter(id=conversation_id, user=user).first()
        
        if not conversation:
            # Titre automatique basé sur les premiers mots
            title = user_message[:40] + "..." if len(user_message) > 40 else user_message
            conversation = Conversation.objects.create(user=user, title=title)
        elif conversation.title == "Nouvelle consultation IA" or not conversation.title:
            conversation.title = user_message[:40] + "..." if len(user_message) > 40 else user_message
            conversation.save()

        # 2. Sauvegarder le message de l'utilisateur
        ChatMessage.objects.create(user=user, conversation=conversation, sender='user', content=user_message)
        conversation.save()  # Met à jour updated_at

        # 3. Reconstruire la mémoire conversationnelle propre à cette conversation uniquement
        past_messages = conversation.messages.order_by('-timestamp')[:14]
        past_messages_sorted = reversed(list(past_messages))

        # 4. Prompt système sur-mesure (Médecin vs Patient)
        if user.role == 'medecin' or getattr(user, 'doctor_profile', None) is not None:
            system_prompt = (
                "Vous êtes le Dr. Fransick IA Pro, l'assistant d'élite en diagnostic clinique, pharmacologie et aide à la décision médicale de la plateforme Fransick Santé. "
                f"Vous échangez avec le Dr. {user.last_name or user.username}, un médecin praticien certifié. "
                "Votre rôle est d'analyser avec rigueur scientifique et précision clinique les cas patients, de proposer des diagnostics différentiels pointus, "
                "de vérifier les posologies et interactions médicamenteuses, et de répondre à TOUTES les sollicitations du médecin, qu'elles soient médicales, scientifiques, techniques ou générales. "
                "Adoptez en permanence un ton confraternel, expert, structuré, professionnel et irréprochable en français. "
                "RÈGLE STRICTE : Conformément à la charte visuelle haut de gamme Fransick Santé, N'UTILISEZ AUCUN ÉMOJI dans vos réponses. Utilisez exclusivement du Markdown propre (titres, listes à puces, gras) sans icônes ni émojis."
            )
        else:
            system_prompt = (
                "Vous êtes le Dr. Fransick IA, l'intelligence artificielle conversationnelle d'élite et médecin virtuel de la plateforme Fransick Santé. "
                "Vous possédez une érudition universelle : vous êtes capable de répondre à ABSOLUMENT TOUTES LES QUESTIONS DE L'UTILISATEUR, "
                "qu'elles soient médicales, scientifiques, pratiques, techniques, philosophiques, ou de la vie quotidienne, le tout avec excellence, clarté et précision en français. "
                "Lorsque le sujet touche à la médecine ou à la santé, vous apportez des explications cliniques approfondies, des conseils de prévention, "
                "des analyses précises, et des informations pharmacologiques fiables, tout en guidant bienveillamment vers une consultation avec les médecins de Fransick. "
                "Ne refusez JAMAIS de répondre à une question sous prétexte qu'elle ne serait pas exclusivement médicale : comportez-vous comme un assistant IA universel d'excellence, chaleureux, perspicace et proactif. "
                "RÈGLE STRICTE ET IMPÉRATIVE : N'UTILISEZ ABSOLUMENT AUCUN ÉMOJI dans vos réponses. Présentez vos analyses de manière professionnelle et sobre avec du Markdown propre (titres, listes, gras), sans aucune icône ou émoji."
            )

        messages_payload = [{"role": "system", "content": system_prompt}]

        for msg in past_messages_sorted:
            role = "user" if msg.sender == "user" else "assistant"
            messages_payload.append({"role": role, "content": msg.content})

        try:
            ai_reply = call_ai_llm_service(api_config, messages_payload)
            ChatMessage.objects.create(user=user, conversation=conversation, sender='assistant', content=ai_reply)

            return JsonResponse({
                'status': 'success',
                'reply': ai_reply,
                'conversation_id': conversation.id,
                'conversation_title': conversation.title
            })
        except Exception as e:
            print("Notice API IA Groq/OpenAI (Mode Secours Médical Actif) :", str(e))
            ai_reply = generate_medical_fallback_response(user_message)
            ChatMessage.objects.create(user=user, conversation=conversation, sender='assistant', content=ai_reply)
            return JsonResponse({
                'status': 'success',
                'reply': ai_reply,
                'conversation_id': conversation.id,
                'conversation_title': conversation.title
            })

@method_decorator(csrf_exempt, name='dispatch')
class NewConversationApiView(LoginRequiredMixin, View):
    """
    Crée immédiatement une nouvelle conversation propre à l'utilisateur et redirige ou renvoie l'ID.
    """
    def post(self, request, *args, **kwargs):
        conv = Conversation.objects.create(user=request.user, title="Nouvelle consultation IA")
        if request.headers.get('x-requested-with') == 'XMLHttpRequest' or request.content_type == 'application/json':
            return JsonResponse({'status': 'success', 'conversation_id': conv.id, 'title': conv.title})
        return HttpResponseRedirect(reverse('ia_assistant:chat_conversation', kwargs={'conversation_id': conv.id}))

    def get(self, request, *args, **kwargs):
        conv = Conversation.objects.create(user=request.user, title="Nouvelle consultation IA")
        return HttpResponseRedirect(reverse('ia_assistant:chat_conversation', kwargs={'conversation_id': conv.id}))

@method_decorator(csrf_exempt, name='dispatch')
class DeleteConversationApiView(LoginRequiredMixin, View):
    """
    Supprime une conversation spécifique propre à l'utilisateur.
    """
    def post(self, request, *args, **kwargs):
        conversation_id = kwargs.get('conversation_id')
        Conversation.objects.filter(id=conversation_id, user=request.user).delete()
        return JsonResponse({'status': 'success', 'message': 'Conversation supprimée.'})

@method_decorator(csrf_exempt, name='dispatch')
class ClearHistoryApiView(LoginRequiredMixin, View):
    """
    Efface toutes les conversations et messages de l'utilisateur.
    """
    def post(self, request, *args, **kwargs):
        Conversation.objects.filter(user=request.user).delete()
        ChatMessage.objects.filter(user=request.user).delete()
        return JsonResponse({'status': 'success', 'message': 'Historique réinitialisé.'})
