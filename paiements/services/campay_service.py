"""
Service d'intégration CamPay API — Fransick Santé
Documentation: https://campay.net/api/docs

Principes de sécurité :
  - La clé API est lue dynamiquement depuis settings à chaque appel (jamais à l'import)
  - Aucune donnée sensible (token, clé) n'est loggée
  - Le campay_raw_response est nettoyé avant stockage
  - Tout appel CamPay se fait exclusivement côté backend (jamais côté frontend)

Bascule sandbox/production : mettre CAMPAY_ENV=sandbox ou CAMPAY_ENV=production dans .env
"""
import re
import logging
import requests
from django.conf import settings

logger = logging.getLogger(__name__)


# ─────────────────────────────────────────────────────────────────────────────
# CONSTANTES — OPÉRATEURS CAMEROUNAIS
# Source: ARCEP Cameroun + CamPay doc officielle
# ─────────────────────────────────────────────────────────────────────────────

# Préfixes MTN MoMo Cameroun (sur 9 chiffres, sans indicatif)
MTN_PREFIXES = (
    '650', '651', '652', '653', '654',  # MTN
    '670', '671', '672', '673', '674', '675', '676', '677', '678', '679',
    '680', '681', '682', '683', '684', '685', '686', '687', '688', '689',
)

# Préfixes Orange Money Cameroun (sur 9 chiffres, sans indicatif)
ORANGE_PREFIXES = (
    '655', '656', '657', '658', '659',
    '690', '691', '692', '693', '694', '695', '696', '697', '698', '699',
)

# Correspondance statuts CamPay → statuts internes Fransick
CAMPAY_STATUS_MAP = {
    'SUCCESSFUL': 'successful',
    'FAILED':     'failed',
    'PENDING':    'pending',
    'EXPIRED':    'expired',
    'CANCELLED':  'cancelled',
}

# Messages d'erreur lisibles selon le code CamPay
CAMPAY_ERROR_MESSAGES = {
    'insufficient_balance':    'Solde Mobile Money insuffisant. Rechargez votre compte et réessayez.',
    'invalid_phone':           'Ce numéro n\'est pas enregistré chez l\'opérateur Mobile Money.',
    'invalid_amount':          'Le montant est invalide ou inférieur au minimum autorisé.',
    'user_cancelled':          'Vous avez annulé la transaction sur votre téléphone.',
    'timeout':                 'Le délai de confirmation a expiré. Veuillez réessayer.',
    'transaction_not_found':   'Transaction introuvable. Contactez le support Fransick.',
    'duplicate_transaction':   'Une transaction similaire est déjà en cours. Attendez quelques instants.',
    'service_unavailable':     'Le service CamPay est temporairement indisponible. Réessayez dans quelques minutes.',
    'invalid_token':           'Problème d\'authentification avec le service de paiement. Contactez le support.',
    'network_error':           'Erreur réseau lors du paiement. Vérifiez votre connexion et réessayez.',
}


# ─────────────────────────────────────────────────────────────────────────────
# ACCÈS AUX PARAMÈTRES (dynamique — pas d'import global stale)
# ─────────────────────────────────────────────────────────────────────────────

def _get_base_url() -> str:
    """Retourne l'URL de base CamPay selon l'environnement configuré."""
    return getattr(settings, 'CAMPAY_API_BASE_URL', 'https://demo.campay.net/api')


def _get_api_token() -> str:
    """Retourne le token API CamPay depuis les settings (chargé dynamiquement)."""
    token = getattr(settings, 'CAMPAY_API_TOKEN', '')
    if not token:
        # Fallback : obtenir un token temporaire via username/password
        return _get_token_from_credentials()
    return token


def _get_token_from_credentials() -> str:
    """Récupère un jeton temporaire via les identifiants username/password CamPay."""
    username = getattr(settings, 'CAMPAY_USERNAME', '')
    password = getattr(settings, 'CAMPAY_PASSWORD', '')
    if not username or not password:
        raise ValueError(
            "[CamPay] Aucun token API ni identifiants configurés. "
            "Vérifiez CAMPAY_API_TOKEN dans votre .env"
        )
    url = f'{_get_base_url()}/token/'
    response = requests.post(
        url,
        json={'username': username, 'password': password},
        timeout=15
    )
    data = response.json()
    if response.status_code == 200 and data.get('token'):
        return data['token']
    logger.error("[CamPay] Échec authentification par identifiants (token non retourné)")
    raise ValueError("Impossible d'obtenir le jeton CamPay par identifiants.")


def _get_headers() -> dict:
    """Retourne les en-têtes HTTP sécurisés pour les appels CamPay."""
    token = _get_api_token()
    return {
        'Authorization': f'Token {token}',
        'Content-Type': 'application/json',
    }


def _sanitize_raw_response(data: dict) -> dict:
    """
    Nettoie la réponse brute CamPay avant stockage en DB.
    Supprime les champs pouvant contenir des données sensibles.
    """
    sensitive_keys = {'token', 'access_token', 'refresh_token', 'secret', 'api_key', 'password'}
    return {k: v for k, v in data.items() if k.lower() not in sensitive_keys}


def _map_error_message(data: dict, default: str = '') -> str:
    """
    Traduit un code d'erreur CamPay en message lisible pour le patient.
    Cherche dans 'error_code', 'code', puis dans 'message'.
    """
    error_code = (data.get('error_code') or data.get('code') or '').lower().replace(' ', '_')
    if error_code and error_code in CAMPAY_ERROR_MESSAGES:
        return CAMPAY_ERROR_MESSAGES[error_code]

    # Recherche par mots-clés dans le message CamPay
    raw_message = (data.get('message') or data.get('detail') or default).lower()
    if 'insufficient' in raw_message or 'solde' in raw_message:
        return CAMPAY_ERROR_MESSAGES['insufficient_balance']
    if 'invalid' in raw_message and 'phone' in raw_message:
        return CAMPAY_ERROR_MESSAGES['invalid_phone']
    if 'cancelled' in raw_message or 'cancel' in raw_message:
        return CAMPAY_ERROR_MESSAGES['user_cancelled']
    if 'timeout' in raw_message or 'expired' in raw_message:
        return CAMPAY_ERROR_MESSAGES['timeout']
    if 'token' in raw_message or 'unauthorized' in raw_message or 'authentication' in raw_message:
        return CAMPAY_ERROR_MESSAGES['invalid_token']

    # Retourne le message CamPay original s'il est lisible, sinon un message générique
    user_message = data.get('message') or data.get('detail') or default
    if user_message and len(user_message) < 200:
        return user_message
    return 'Une erreur est survenue lors du paiement. Veuillez réessayer.'


# ─────────────────────────────────────────────────────────────────────────────
# NORMALISATION DU NUMÉRO DE TÉLÉPHONE
# ─────────────────────────────────────────────────────────────────────────────

def normalize_phone(phone: str) -> str:
    """
    Normalise un numéro de téléphone camerounais pour CamPay.
    CamPay exige le format international sans '+' : 237XXXXXXXXX (12 chiffres)

    Formats acceptés en entrée :
      - 677000000       (9 chiffres, format court)
      - 237677000000    (12 chiffres, format international sans +)
      - +237677000000   (format international avec +)
      - 00237677000000  (format 00 + indicatif)
      - 677 000 000     (avec espaces)
      - 677-000-000     (avec tirets)
    """
    # Nettoyer les espaces, tirets, parenthèses
    phone = re.sub(r'[\s\-\(\)]', '', phone.strip())

    # Supprimer le préfixe +
    if phone.startswith('+'):
        phone = phone[1:]

    # Supprimer le préfixe 00
    if phone.startswith('00237'):
        phone = phone[2:]  # → 237XXXXXXXXX

    # Ajouter l'indicatif 237 si numéro court (9 chiffres commençant par 6)
    if re.match(r'^6\d{8}$', phone):
        phone = '237' + phone

    # Vérification finale : doit être 237 + 9 chiffres
    if not re.match(r'^237[26789]\d{8}$', phone):
        logger.warning(f"[CamPay] Numéro normalisé potentiellement invalide: {phone}")

    return phone


def detect_operator(phone: str) -> str:
    """
    Détecte l'opérateur Mobile Money à partir du préfixe du numéro camerounais.
    Retourne 'MTN', 'ORANGE' ou '' (inconnu — CamPay détectera automatiquement).

    Note : CamPay peut détecter l'opérateur automatiquement depuis le numéro.
    Cette fonction est utilisée pour l'affichage côté frontend uniquement.
    """
    normalized = normalize_phone(phone)
    # Extraire les 3 chiffres après l'indicatif 237 (position 3-6)
    if len(normalized) >= 6 and normalized.startswith('237'):
        prefix3 = normalized[3:6]  # ex: '677' depuis '237677000000'
        if prefix3 in MTN_PREFIXES:
            return 'MTN'
        if prefix3 in ORANGE_PREFIXES:
            return 'ORANGE'
    return ''  # Opérateur inconnu — CamPay détectera


# ─────────────────────────────────────────────────────────────────────────────
# INITIATION D'UN PAIEMENT
# ─────────────────────────────────────────────────────────────────────────────

def initiate_collection(
    amount: int,
    phone: str,
    description: str,
    external_reference: str,
) -> dict:
    """
    Initie une demande de collecte Mobile Money (USSD push) via CamPay.

    Args:
        amount:             Montant en XAF (entier, > 0)
        phone:              Numéro de téléphone (tout format camerounais accepté)
        description:        Description affichée dans le USSD (max 100 chars)
        external_reference: Référence UUID interne Fransick (retrouver la transaction)

    Returns:
        dict avec les clés :
          'success'    (bool)
          'reference'  (str|None)  — référence CamPay
          'ussd_code'  (str|None)  — code USSD à composer si pas de push
          'message'    (str)       — message lisible pour le patient
          'operator'   (str)       — opérateur détecté ('MTN'|'ORANGE'|'')
          'raw'        (dict)      — réponse brute nettoyée (sans données sensibles)
    """
    # Normaliser le numéro
    phone_normalized = normalize_phone(phone)
    operator_detected = detect_operator(phone_normalized)

    env_label = getattr(settings, 'CAMPAY_ENV', 'sandbox')
    logger.info(
        f"[CamPay/{env_label}] Initiation collecte — "
        f"montant={amount} XAF, phone={phone_normalized}, opérateur={operator_detected or 'auto'}"
    )

    payload = {
        'amount':             str(amount),
        'currency':           'XAF',
        'from':               phone_normalized,
        'description':        str(description)[:100],
        'external_reference': str(external_reference),
    }

    try:
        url = f'{_get_base_url()}/collect/'
        response = requests.post(
            url,
            json=payload,
            headers=_get_headers(),
            timeout=30,
        )
        data = response.json()
        safe_data = _sanitize_raw_response(data)

        # Log sans données sensibles
        logger.info(f"[CamPay] Réponse collect (status={response.status_code}): {safe_data}")

        if response.status_code in (200, 201) and data.get('reference'):
            return {
                'success':   True,
                'reference': data.get('reference'),
                'ussd_code': data.get('ussd_code'),
                'message':   data.get('message', 'Demande envoyée. Vérifiez votre téléphone.'),
                'operator':  data.get('operator', operator_detected),
                'raw':       safe_data,
            }
        else:
            error_msg = _map_error_message(data, 'Erreur lors de l\'initiation du paiement.')
            logger.warning(f"[CamPay] Collecte refusée (status={response.status_code}): {safe_data}")
            return {
                'success':   False,
                'reference': None,
                'ussd_code': None,
                'message':   error_msg,
                'operator':  operator_detected,
                'raw':       safe_data,
            }

    except requests.exceptions.Timeout:
        logger.error("[CamPay] Timeout lors de l'initiation du paiement")
        return {
            'success': False, 'reference': None, 'ussd_code': None,
            'operator': operator_detected, 'raw': {},
            'message': CAMPAY_ERROR_MESSAGES['network_error'],
        }
    except requests.exceptions.ConnectionError:
        logger.error("[CamPay] Erreur de connexion réseau")
        return {
            'success': False, 'reference': None, 'ussd_code': None,
            'operator': operator_detected, 'raw': {},
            'message': 'Impossible de joindre le service CamPay. Vérifiez votre connexion internet.',
        }
    except Exception as e:
        logger.error(f"[CamPay] Exception inattendue lors de l'initiation: {e}")
        return {
            'success': False, 'reference': None, 'ussd_code': None,
            'operator': operator_detected, 'raw': {},
            'message': 'Erreur technique lors du paiement. Veuillez réessayer.',
        }


# ─────────────────────────────────────────────────────────────────────────────
# VÉRIFICATION DU STATUT D'UNE TRANSACTION
# ─────────────────────────────────────────────────────────────────────────────

def check_transaction_status(campay_reference: str) -> dict:
    """
    Vérifie le statut d'une transaction CamPay.

    Args:
        campay_reference: La référence retournée par CamPay lors de l'initiation

    Returns:
        dict avec :
          'status'    (str)  — 'SUCCESSFUL'|'FAILED'|'PENDING'|'EXPIRED'|'CANCELLED'
          'operator'  (str)  — opérateur confirmé
          'amount'    (str)  — montant confirmé
          'currency'  (str)  — devise
          'message'   (str)  — message lisible
          'raw'       (dict) — réponse brute nettoyée
    """
    try:
        url = f'{_get_base_url()}/transaction/{campay_reference}/'
        response = requests.get(url, headers=_get_headers(), timeout=15)
        data = response.json()
        safe_data = _sanitize_raw_response(data)

        status = (data.get('status') or 'PENDING').upper()
        logger.info(f"[CamPay] Status check {campay_reference}: {status}")

        return {
            'status':   status,
            'operator': data.get('operator', ''),
            'amount':   data.get('amount', ''),
            'currency': data.get('currency', 'XAF'),
            'message':  _map_error_message(data, ''),
            'raw':      safe_data,
        }

    except requests.exceptions.Timeout:
        logger.error(f"[CamPay] Timeout vérification statut {campay_reference}")
        return {'status': 'PENDING', 'operator': '', 'message': 'Vérification en cours...', 'raw': {}}
    except Exception as e:
        logger.error(f"[CamPay] Erreur vérification statut {campay_reference}: {e}")
        return {'status': 'PENDING', 'operator': '', 'message': str(e), 'raw': {}}


# ─────────────────────────────────────────────────────────────────────────────
# EXPIRATION DES PAIEMENTS BLOQUÉS (à appeler dans le polling view)
# ─────────────────────────────────────────────────────────────────────────────

PAYMENT_EXPIRY_MINUTES = 5  # Délai avant expiration automatique d'un paiement pending


def should_expire_payment(paiement) -> bool:
    """
    Retourne True si le paiement est en attente depuis plus de PAYMENT_EXPIRY_MINUTES.
    À appeler dans CheckPaymentStatusAjaxView pour éviter les paiements bloqués.
    """
    from django.utils import timezone
    import datetime

    if paiement.status != 'pending':
        return False
    age = timezone.now() - paiement.created_at
    return age > datetime.timedelta(minutes=PAYMENT_EXPIRY_MINUTES)
