import os
from pathlib import Path
from dotenv import load_dotenv

# ==============================================================================
# VARIÁVEIS DE AMBIENTE
# ==============================================================================
load_dotenv()

# ==============================================================================
# SEGURANÇA
# ==============================================================================
SECRET_KEY = os.environ.get(
    'SECRET_KEY',
    'django-insecure-chave-dev-nao-usar-em-producao-xxxx'
)

DEBUG = os.environ.get('DEBUG', 'True').lower() in ('true', '1', 'yes')

ALLOWED_HOSTS = [
    h.strip() for h in os.environ.get(
        'ALLOWED_HOSTS',
        'localhost,127.0.0.1'
    ).split(',') if h.strip()
]

CSRF_TRUSTED_ORIGINS = [
    o.strip() for o in os.environ.get(
        'CSRF_TRUSTED_ORIGINS',
        ''
    ).split(',') if o.strip()
]

# ==============================================================================
# CONFIGURAÇÕES BÁSICAS E SEGURANÇA
# ==============================================================================
BASE_DIR = Path(__file__).resolve().parent.parent

# ATENÇÃO: Em produção, defina uma SECRET_KEY longa e aleatória no seu .env
SECRET_KEY = os.getenv('SECRET_KEY', 'django-insecure-reabitech-tcc-final-2024')

DEBUG = os.getenv('DEBUG', 'True') == 'True'

ALLOWED_HOSTS = os.getenv('ALLOWED_HOSTS', 'localhost,127.0.0.1').split(',')

# Aplicativos instalados
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'whitenoise.runserver_nostatic',

    # Apps do REABITECH
    'usuarios',
    'projetos',
    'dashboard',
    'prontuario',
    'fisioterapia',
    'psicologia',
    'painel',
    'consultas',
    'mensageria',   # 🔥 NOVO — Mensageria interna
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
    'usuarios.middleware.AuditoriaMiddleware',
]

ROOT_URLCONF = 'backend.urls'

# Configuração de Templates
TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates'],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.template.context_processors.csrf',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
                'dashboard.context_processors.notificacoes_context',
                'dashboard.context_processors.projeto_ativo_context',
                'mensageria.context_processors.mensageria_context',   # 🔥 NOVO
            ],
        },
    },
]

WSGI_APPLICATION = 'backend.wsgi.application'

# ==============================================================================
# VALIDAÇÃO DE SENHAS E AUTENTICAÇÃO
# ==============================================================================
AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator'},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]

# Configurações de Login e Redirecionamento
LOGIN_URL = '/login/'
LOGIN_REDIRECT_URL = '/dashboard/'
LOGOUT_REDIRECT_URL = '/'

# ==============================================================================
# INTERNACIONALIZAÇÃO E LOCALIZAÇÃO
# ==============================================================================
LANGUAGE_CODE = 'pt-br'
TIME_ZONE = 'America/Sao_Paulo'
USE_I18N = True
USE_TZ = True

# ==============================================================================
# ARQUIVOS ESTÁTICOS E MÍDIA
# ==============================================================================
STATIC_URL = '/static/'
STATICFILES_DIRS = [BASE_DIR / 'static']
STATIC_ROOT = BASE_DIR / 'staticfiles'

MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'

# ==============================================================================
# CONFIGURAÇÃO DE E-MAIL
# ==============================================================================
if DEBUG:
    EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'
else:
    pass

DEFAULT_FROM_EMAIL = os.getenv('DEFAULT_FROM_EMAIL', 'noreply@reabitech.com')

# ==============================================================================
# CONFIGURAÇÕES DE SEGURANÇA PARA PRODUÇÃO
# ==============================================================================
if not DEBUG:
    SECURE_SSL_REDIRECT = True
    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_SECURE = True
    SECURE_HSTS_SECONDS = 31536000
    SECURE_HSTS_INCLUDE_SUBDOMAINS = True
    SECURE_HSTS_PRELOAD = True
    X_FRAME_OPTIONS = 'DENY'
    SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')

# ==============================================================================
# CAMPO DE ID PADRÃO
# ==============================================================================
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# ==============================================================================
# UTILITÁRIOS DE DESENVOLVIMENTO
# ==============================================================================
INTERNAL_IPS = ['127.0.0.1']

# ==============================================================================
# CONFIGURAÇÕES DE DESENVOLVIMENTO — COOKIES E CSRF
# ==============================================================================
CSRF_COOKIE_HTTPONLY = False
CSRF_COOKIE_SAMESITE = 'Lax'
SESSION_COOKIE_SAMESITE = 'Lax'

CSRF_TRUSTED_ORIGINS = [
    'http://127.0.0.1:8000',
    'http://localhost:8000',
]

# ==============================================================================
# BANCO DE DADOS — suporta SQLite (dev) e PostgreSQL (produção)
# ==============================================================================
DATABASE_URL = os.environ.get('DATABASE_URL', '').strip()

if DATABASE_URL:
    import dj_database_url
    DATABASES = {
        'default': dj_database_url.parse(
            DATABASE_URL,
            conn_max_age=600,
            conn_health_checks=True,
        )
    }
else:
    # Fallback: SQLite (dev)
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.sqlite3',
            'NAME': BASE_DIR / 'db.sqlite3',
        }
    }

# ==============================================================================
# ARQUIVOS ESTÁTICOS (WhiteNoise)
# ==============================================================================
STATICFILES_STORAGE = 'whitenoise.storage.CompressedStaticFilesStorage'

# ==============================================================================
# UPLOAD — Tamanho máximo de arquivo (10MB para anexos da mensageria)
# ==============================================================================
FILE_UPLOAD_MAX_MEMORY_SIZE = 10 * 1024 * 1024      # 10MB em memória
DATA_UPLOAD_MAX_MEMORY_SIZE = 10 * 1024 * 1024      # 10MB no POST
