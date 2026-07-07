"""
Django settings for domap project.
"""

import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent

SECRET_KEY = os.environ.get(
    'SECRET_KEY',
    'django-insecure-bv0)^ty_k2003anf@m#v8)_q6%959c%=bici%)0*&b&4iz50qd',
)

DEBUG = os.environ.get('DEBUG', 'True') == 'True'

ALLOWED_HOSTS = os.environ.get('ALLOWED_HOSTS', 'localhost,127.0.0.1').split(',')

# Detrás de Nginx/Cloudflare, Gunicorn solo ve tráfico HTTP plano del proxy
# interno; este header le dice a Django que la conexión original del cliente
# sí fue HTTPS (si no, request.is_secure() da False y el CSRF de origen falla).
SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')

# Django 4+ exige que el Origin de las peticiones POST coincida con uno de
# estos orígenes confiables (con esquema incluido), o el CSRF falla con 403.
CSRF_TRUSTED_ORIGINS = [
    origin.strip() for origin in os.environ.get('CSRF_TRUSTED_ORIGINS', '').split(',') if origin.strip()
] or [f'https://{host}' for host in ALLOWED_HOSTS if host not in ('localhost', '127.0.0.1')]


# Application definition

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'widget_tweaks',
    'core',
    'catalog',
    'cart',
    'orders',
    'analytics',
    'panel',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'analytics.middleware.TrackingMiddleware',
]

ROOT_URLCONF = 'domap.urls'

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
                'cart.context_processors.cart_badges',
                'analytics.context_processors.tracking',
                'core.context_processors.static_version',
                'core.context_processors.contact_info',
            ],
        },
    },
]

WSGI_APPLICATION = 'domap.wsgi.application'


# Database

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }
}


# Password validation

AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator'},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]


# Internationalization

LANGUAGE_CODE = 'es-pe'

TIME_ZONE = 'America/Lima'

USE_I18N = True

USE_TZ = True


# Static & media files

STATIC_URL = 'static/'
STATICFILES_DIRS = [BASE_DIR / 'static']
STATIC_ROOT = BASE_DIR / 'staticfiles'

STORAGES = {
    'default': {
        'BACKEND': 'django.core.files.storage.FileSystemStorage',
    },
    'staticfiles': {
        'BACKEND': 'whitenoise.storage.CompressedManifestStaticFilesStorage',
    },
}

MEDIA_URL = 'media/'
MEDIA_ROOT = BASE_DIR / 'media'

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# Cache-buster para CSS/JS estáticos: súbelo cada vez que cambien para que el
# navegador del cliente no siga sirviendo una versión vieja desde su caché.
STATIC_VERSION = '22'


# Sessions
# Required so an anonymous visitor gets a stable session_key from their very
# first request — otherwise a session with no data writes never persists,
# and unique-visitor tracking breaks for first-time visitors.
SESSION_SAVE_EVERY_REQUEST = True
SESSION_COOKIE_AGE = 60 * 60 * 24 * 30  # 30 días

LOGIN_URL = '/admin/login/'

# Constantes del negocio "Mordé"
WHATSAPP_NUMBER = '51954926839'
INSTAGRAM_URL = 'https://www.instagram.com/morde.waffles/'
INSTAGRAM_HANDLE = 'morde.waffles'
ABANDONMENT_WINDOW_MINUTES = 60

# WhatsApp automático vía Evolution API (Docker).
# El administrador conecta su número escaneando el QR en /pedidos/staff/whatsapp/
# y, cuando un cliente hace un pedido en la web, ese número le envía el detalle.
#   EVOLUTION_API_URL  URL interna de Evolution (nombre del servicio de Compose).
#   EVOLUTION_API_KEY  clave global de la API (la misma AUTHENTICATION_API_KEY).
#   EVOLUTION_INSTANCE nombre de la instancia (el "teléfono" conectado).
#   WHATSAPP_COUNTRY_CODE código de país por defecto para normalizar el número.
#   WHATSAPP_NOTIFY_ENABLED interruptor para activar el envío automático.
EVOLUTION_API_URL = os.environ.get('EVOLUTION_API_URL', 'http://evolution-api:8080')
EVOLUTION_API_KEY = os.environ.get('EVOLUTION_API_KEY', '')
EVOLUTION_INSTANCE = os.environ.get('EVOLUTION_INSTANCE', 'morde')
WHATSAPP_COUNTRY_CODE = os.environ.get('WHATSAPP_COUNTRY_CODE', '51')
WHATSAPP_NOTIFY_ENABLED = os.environ.get('WHATSAPP_NOTIFY_ENABLED', 'False') == 'True'

# Email (confirmación de pedidos)
if DEBUG:
    EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'
else:
    EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
    EMAIL_HOST = os.environ.get('EMAIL_HOST', '')
    EMAIL_PORT = int(os.environ.get('EMAIL_PORT', '587'))
    EMAIL_HOST_USER = os.environ.get('EMAIL_HOST_USER', '')
    EMAIL_HOST_PASSWORD = os.environ.get('EMAIL_HOST_PASSWORD', '')
    EMAIL_USE_TLS = os.environ.get('EMAIL_USE_TLS', 'True') == 'True'
DEFAULT_FROM_EMAIL = os.environ.get('DEFAULT_FROM_EMAIL', 'pedidos@morde.pe')

# Rutas que el middleware de tracking debe ignorar por completo. Nota:
# /analytics/panel/ (el dashboard de staff) se excluye para no inflar las
# visitas, pero los endpoints de eventos (/analytics/evento/..., /beacon/...)
# SÍ necesitan sesión de visitante para poder registrar el clic — no excluir
# todo el prefijo /analytics/ o esos eventos nunca se guardan.
TRACKING_EXCLUDED_PREFIXES = ('/admin/', '/static/', '/media/', '/analytics/panel/', '/panel/')
