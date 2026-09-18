"""
Service d'intégration CamPay API
Documentation: https://campay.net
Utilise le token permanent (Authorization: Token <token>)
"""
import requests
import logging
from django.conf import settings

logger = logging.getLogger(__name__)

CAMPAY_BASE_URL = getattr(settings, 'CAMPAY_API_BASE_URL', 'https://campay.net/api')
CAMPAY_USERNAME = getattr(settings, 'CAMPAY_USERNAME', '')
CAMPAY_PASSWORD = getattr(settings, 'CAMPAY_PASSWORD', '')
CAMPAY_API_TOKEN = getattr(settings, 'CAMPAY_API_TOKEN', '')

def _get_campay_token():
    """Récupère un jeton temporaire depuis CamPay avec les identifiants de l'application."""
    if not CAMPAY_USERNAME or not CAMPAY_PASSWORD:
        raise ValueError("Les identifiants CamPay (Username/Password) ne sont pas configurés.")
        
    url = f'{CAMPAY_BASE_URL}/token/'
    response = requests.post(url, json={'username': CAMPAY_USERNAME, 'password': CAMPAY_PASSWORD}, timeout=15)
    data = response.json()
    
    if response.status_code == 200 and data.get('token'):
        return data['token']
    else:
        logger.error(f"[CamPay] Erreur d'authentification: {data}")
        raise ValueError(f"Impossible d'obtenir le jeton CamPay: {data.get('detail', 'Erreur inconnue')}")

def _get_headers():
    """Retourne les en-têtes HTTP avec le token d'authentification CamPay."""
    token = CAMPAY_API_TOKEN
    if not token:
        token = _get_campay_token()
    return {
        'Authorization': f'Token {token}',
        'Content-Type': 'application/json',
    }


def initiate_collection(amount: int, phone: str, description: str, external_reference: str) -> dict:
    """
    Initie une demande de collecte Mobile Money (USSD push) via CamPay.

    Args:
        amount: Montant en XAF (entier)
        phone: Numéro de téléphone au format international (ex: 237677000000)
        description: Description affichée dans le USSD
        external_reference: Référence interne unique (UUID du paiement)

    Returns:
        dict avec les clés: 'success', 'reference', 'ussd_code', 'message', 'raw'
    """
    # Normaliser le numéro de téléphone
    phone = normalize_phone(phone)

    payload = {
        'amount': str(amount),
        'currency': 'XAF',
        'from': phone,
        'description': description,
        'external_reference': str(external_reference),
    }

    try:
        url = f'{CAMPAY_BASE_URL}/collect/'
        response = requests.post(url, json=payload, headers=_get_headers(), timeout=30)
        data = response.json()

        logger.info(f"[CamPay] Initiate collection response: {data}")

        if response.status_code in (200, 201) and data.get('reference'):
            return {
                'success': True,
                'reference': data.get('reference'),
                'ussd_code': data.get('ussd_code'),
                'message': data.get('message', 'Demande envoyée'),
                'raw': data,
            }
        else:
            return {
                'success': False,
                'reference': None,
                'message': data.get('message', 'Erreur lors de l\'initiation du paiement'),
                'raw': data,
            }

    except requests.exceptions.Timeout:
        logger.error("[CamPay] Timeout lors de l'initiation du paiement")
        return {
            'success': False,
            'reference': None,
            'message': 'Le service de paiement ne répond pas. Veuillez réessayer.',
            'raw': {},
        }
    except requests.exceptions.ConnectionError:
        logger.error("[CamPay] Erreur de connexion")
        return {
            'success': False,
            'reference': None,
            'message': 'Impossible de joindre le service CamPay. Vérifiez votre connexion.',
            'raw': {},
        }
    except Exception as e:
        logger.error(f"[CamPay] Exception inattendue: {e}")
        return {
            'success': False,
            'reference': None,
            'message': f'Erreur technique: {str(e)}',
            'raw': {},
        }


def check_transaction_status(campay_reference: str) -> dict:
    """
    Vérifie le statut d'une transaction CamPay.

    Args:
        campay_reference: La référence retournée par CamPay lors de l'initiation

    Returns:
        dict avec 'status' (SUCCESSFUL/FAILED/PENDING), 'operator', 'raw'
    """
    try:
        url = f'{CAMPAY_BASE_URL}/transaction/{campay_reference}/'
        response = requests.get(url, headers=_get_headers(), timeout=15)
        data = response.json()

        logger.info(f"[CamPay] Status check for {campay_reference}: {data}")

        return {
            'status': data.get('status', 'PENDING'),
            'operator': data.get('operator', ''),
            'amount': data.get('amount', ''),
            'currency': data.get('currency', 'XAF'),
            'message': data.get('message', ''),
            'raw': data,
        }

    except Exception as e:
        logger.error(f"[CamPay] Erreur vérification statut {campay_reference}: {e}")
        return {
            'status': 'PENDING',
            'operator': '',
            'message': str(e),
            'raw': {},
        }


def normalize_phone(phone: str) -> str:
    """
    Normalise un numéro de téléphone pour CamPay.
    CamPay exige le format international sans '+' (ex: 237677000000)
    """
    phone = phone.strip().replace(' ', '').replace('-', '').replace('+', '')
    # Si le numéro commence par 6 ou 2 (format camerounais court), ajouter 237
    if phone.startswith('6') and len(phone) == 9:
        phone = '237' + phone
    elif phone.startswith('2') and len(phone) == 8:
        phone = '237' + phone
    return phone


# Correspondance statuts CamPay → statuts internes
CAMPAY_STATUS_MAP = {
    'SUCCESSFUL': 'successful',
    'FAILED': 'failed',
    'PENDING': 'pending',
    'EXPIRED': 'expired',
}
