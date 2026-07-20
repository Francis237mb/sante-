from .base import *

# Production settings
DEBUG = False

# Security settings
SECURE_SSL_REDIRECT = True
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
SECURE_BROWSER_XSS_FILTER = True
SECURE_CONTENT_TYPE_NOSNIFF = True

# Allow configuration via env
ALLOWED_HOSTS = env('ALLOWED_HOSTS', default=['fransick.com'])
