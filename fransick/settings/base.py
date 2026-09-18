import os
from pathlib import Path
import environ
from django.utils.translation import gettext_lazy as _

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent.parent

# Initialize environ
env = environ.Env(
    DEBUG=(bool, False),
    ALLOWED_HOSTS=(list, ['127.0.0.1', 'localhost']),
    CORS_ALLOW_ALL_ORIGINS=(bool, True),
)

# Take environment variables from .env file
environ.Env.read_env(os.path.join(BASE_DIR, '.env'))

SECRET_KEY = env('SECRET_KEY')
DEBUG = env('DEBUG')
ALLOWED_HOSTS = env('ALLOWED_HOSTS')

# Application definition
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    
    # Third-party apps
    'rest_framework',
    'corsheaders',
    'widget_tweaks',
    
    # Custom apps
    'core',
    'accounts',
    'patients',
    'medecins',
    'pharmacies',
    'consultations',
    'ordonnances',
    'ia_assistant',
    'administration',
    'teleconsultation',
    'paiements',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',  # Serving static files in production
    'django.contrib.sessions.middleware.SessionMiddleware',
    'corsheaders.middleware.CorsMiddleware',
    'django.middleware.locale.LocaleMiddleware',  # Multi-language translation
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'fransick.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates'],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
                'django.template.context_processors.i18n',
                'administration.context_processors.site_appearance',
            ],
        },
    },
]

WSGI_APPLICATION = 'fransick.wsgi.application'

# Database fallback config
DATABASES = {
    'default': env.db('DATABASE_URL', default=f"sqlite:///{BASE_DIR / 'db.sqlite3'}")
}

# Custom User Model
AUTH_USER_MODEL = 'accounts.CustomUser'

# Password validation
AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]

ALLOWED_HOSTS = ['*', '192.168.1.67', '127.0.0.1', 'localhost']

# Internationalization
LANGUAGE_CODE = 'fr'  # Default language is French
TIME_ZONE = 'Europe/Paris'
USE_I18N = True
USE_TZ = True

LANGUAGES = [
    ('fr', _('Français')),
    ('en', _('English')),
]

LOCALE_PATHS = [
    BASE_DIR / 'locale',
]

# Static files (CSS, JavaScript, Images)
STATIC_URL = '/static/'
STATIC_ROOT = BASE_DIR / 'staticfiles'
STATICFILES_DIRS = [
    BASE_DIR / 'static',
]

# Media files (for logo, profile pictures)
MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'

# ALLOWED_HOSTS & CSRF pour Réseau Local Wi-Fi & Téléphone Mobile
ALLOWED_HOSTS = ['*']

CSRF_TRUSTED_ORIGINS = [
    'http://127.0.0.1:8000',
    'http://127.0.0.1',
    'http://localhost:8000',
    'http://localhost',
]

# Détection dynamique des adresses IP locales pour autoriser tous les téléphones et PCs du Wi-Fi
import socket
try:
    hostname = socket.gethostname()
    _, _, ip_list = socket.gethostbyname_ex(hostname)
    for ip in ip_list:
        CSRF_TRUSTED_ORIGINS.append(f'http://{ip}:8000')
        CSRF_TRUSTED_ORIGINS.append(f'http://{ip}')
except Exception:
    pass

# Plages IP courantes de sous-réseaux Wi-Fi et partage de connexion mobile (192.168.x.x & 172.20.10.x & 10.0.x.x)
CSRF_TRUSTED_ORIGINS.append('http://10.0.122.165:8000')
CSRF_TRUSTED_ORIGINS.append('http://10.0.122.165')
for sub in range(256):
    CSRF_TRUSTED_ORIGINS.append(f'http://10.0.{sub}.165:8000')
    CSRF_TRUSTED_ORIGINS.append(f'http://10.0.{sub}.165')
    CSRF_TRUSTED_ORIGINS.append(f'http://10.0.122.{sub}:8000')
    CSRF_TRUSTED_ORIGINS.append(f'http://10.0.122.{sub}')

for sub in [0, 1, 2, 43, 88, 100, 123]:
    for host in range(1, 255):
        CSRF_TRUSTED_ORIGINS.append(f'http://192.168.{sub}.{host}:8000')
        CSRF_TRUSTED_ORIGINS.append(f'http://192.168.{sub}.{host}')
        CSRF_TRUSTED_ORIGINS.append(f'http://172.20.10.{host}:8000')
        CSRF_TRUSTED_ORIGINS.append(f'http://172.20.10.{host}')

CSRF_COOKIE_SECURE = False
SESSION_COOKIE_SECURE = False
CSRF_COOKIE_SAMESITE = 'Lax'
CSRF_COOKIE_HTTPONLY = False

# Default primary key field type
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# Session settings
SESSION_EXPIRE_AT_BROWSER_CLOSE = False  # Conserver la session ouverte
SESSION_COOKIE_AGE = 86400  # Déconnexion après 24 heures d'inactivité (au lieu de 30 min)


# Auth URLs & Redirections
LOGIN_URL = '/accounts/login/patient/'
LOGIN_REDIRECT_URL = 'core:home'
LOGOUT_REDIRECT_URL = 'core:home'

# OpenAI API Key pour l'Assistant IA Médical Fransick
OPENAI_API_KEY = env('OPENAI_API_KEY', default=os.getenv('OPENAI_API_KEY', ''))

# Agora Settings
AGORA_APP_ID = env('AGORA_APP_ID', default=os.getenv('AGORA_APP_ID', ''))
AGORA_APP_CERTIFICATE = env('AGORA_APP_CERTIFICATE', default=os.getenv('AGORA_APP_CERTIFICATE', ''))

# CamPay Payment Gateway
# CAMPAY_ENV=sandbox  → https://demo.campay.net/api  (tests)
# CAMPAY_ENV=production → https://campay.net/api      (production)
CAMPAY_API_TOKEN = env('CAMPAY_API_TOKEN', default=os.getenv('CAMPAY_API_TOKEN', ''))
CAMPAY_USERNAME = env('CAMPAY_USERNAME', default=os.getenv('CAMPAY_USERNAME', ''))
CAMPAY_PASSWORD = env('CAMPAY_PASSWORD', default=os.getenv('CAMPAY_PASSWORD', ''))
CAMPAY_ENV = env('CAMPAY_ENV', default='sandbox')  # 'sandbox' ou 'production'
CAMPAY_API_BASE_URL = (
    'https://campay.net/api'
    if CAMPAY_ENV == 'production'
    else 'https://demo.campay.net/api'
)
# Acompte RDV : 20% du tarif médecin
CAMPAY_DEPOSIT_PERCENT = 20

