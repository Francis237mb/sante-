import os
import json
import openai
from django.conf import settings
from django.views.generic import TemplateView, View
from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
import urllib.request
import urllib.parse
import urllib.error
from .models import ChatMessage
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
        # Récupérer l'historique complet de l'utilisateur connecté
        context['chat_history'] = ChatMessage.objects.filter(user=self.request.user).order_by('timestamp')
        return context

@method_decorator(csrf_exempt, name='dispatch')
class AIChatApiView(LoginRequiredMixin, View):
    """
    Vue API AJAX pour communiquer avec l'Assistant IA alimenté par Groq (Llama-3/Mixtral) ou OpenAI.
    """
    def post(self, request, *args, **kwargs):
        try:
            data = json.loads(request.body.decode('utf-8'))
            user_message = data.get('message', '').strip()
        except Exception:
            user_message = request.POST.get('message', '').strip()

        if not user_message:
            return JsonResponse({'status': 'error', 'message': 'Veuillez saisir une question.'}, status=400)

        api_config = get_ai_api_config()

        # 1. Sauvegarder le message de l'utilisateur en base de données
        ChatMessage.objects.create(user=request.user, sender='user', content=user_message)

        # 2. Reconstruire la mémoire conversationnelle (12 derniers échanges)
        past_messages = ChatMessage.objects.filter(user=request.user).order_by('-timestamp')[:12]
        past_messages_sorted = reversed(list(past_messages))

        system_prompt = (
            "Vous êtes le Dr. Fransick IA, l'intelligence artificielle conversationnelle d'élite et médecin virtuel de la plateforme Fransick Santé. "
            "Vous possédez une érudition universelle : vous êtes capable de répondre à ABSOLUMENT TOUTES LES QUESTIONS DE L'UTILISATEUR, "
            "qu'elles soient médicales, scientifiques, pratiques, techniques, philosophiques, ou de la vie quotidienne, le tout avec excellence, clarté et précision en français. "
            "Lorsque le sujet touche à la médecine ou à la santé, vous apportez des explications cliniques approfondies, des conseils de prévention, "
            "des analyses précises, et des informations pharmacologiques fiables, tout en guidant bienveillamment vers une consultation avec les médecins de Fransick. "
            "Ne refusez JAMAIS de répondre à une question sous prétexte qu'elle ne serait pas exclusivement médicale : comportez-vous comme un assistant IA universel d'excellence, chaleureux, perspicace et proactif."
        )

        messages_payload = [{"role": "system", "content": system_prompt}]
        for msg in past_messages_sorted:
            role = "user" if msg.sender == "user" else "assistant"
            messages_payload.append({"role": role, "content": msg.content})

        try:
            ai_reply = call_ai_llm_service(api_config, messages_payload)

            # 3. Sauvegarder la réponse de l'assistant en base de données
            ChatMessage.objects.create(user=request.user, sender='assistant', content=ai_reply)

            return JsonResponse({
                'status': 'success',
                'reply': ai_reply
            })
        except Exception as e:
            print("Notice API IA Groq/OpenAI (Mode Secours Médical Actif) :", str(e))
            # En cas d'indisponibilité ou absence de clé, déclenchement du Moteur Médical Virtuel Fransick
            ai_reply = generate_medical_fallback_response(user_message)
            ChatMessage.objects.create(user=request.user, sender='assistant', content=ai_reply)
            return JsonResponse({
                'status': 'success',
                'reply': ai_reply
            })

@method_decorator(csrf_exempt, name='dispatch')
class ClearHistoryApiView(LoginRequiredMixin, View):
    """
    Efface l'historique complet de discussion de l'utilisateur.
    """
    def post(self, request, *args, **kwargs):
        ChatMessage.objects.filter(user=request.user).delete()
        return JsonResponse({'status': 'success', 'message': 'Historique réinitialisé.'})
