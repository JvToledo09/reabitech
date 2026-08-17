import os
from pathlib import Path
from dotenv import load_dotenv

# Carrega as variáveis do arquivo .env
load_dotenv()

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
    
    # Apps do projeto
    'usuarios',
    'atletas',
    'fisioterapia',
    'psicologia',
    'dashboard',
    'projetos',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
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
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'backend.wsgi.application'

# ==============================================================================
# BANCO DE DADOS
# ==============================================================================
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }
}
# Para usar PostgreSQL em produção, descomente o bloco abaixo e configure no .env
# DATABASES = {
#     'default': {
#         'ENGINE': 'django.db.backends.postgresql',
#         'NAME': os.getenv('DB_NAME', 'reabitech_db'),
#         'USER': os.getenv('DB_USER', 'postgres'),
#         'PASSWORD': os.getenv('DB_PASSWORD', ''),
#         'HOST': os.getenv('DB_HOST', 'localhost'),
#         'PORT': os.getenv('DB_PORT', '5432'),
#     }
# }


# ==============================================================================
# VALIDAÇÃO DE SENHAS E AUTENTICAÇÃO
# ==============================================================================
AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator'},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]

# Configurações de Login e Redirecionamento (Agora usando o nome da rota 'login')
LOGIN_URL = 'login'
LOGIN_REDIRECT_URL = '/dashboard/'
LOGOUT_REDIRECT_URL = '/'

# ==============================================================================
# INTERNACIONALIZAÇÃO E LOCALIZAÇÃO
# ==============================================================================
LANGUAGE_CODE = 'pt-br'
TIME_ZONE = 'America/Sao_Paulo'
USE_I18N = True
USE_L10N = True  # Formatação de números e datas localizada
USE_TZ = True

# ==============================================================================
# ARQUIVOS ESTÁTICOS E MÍDIA
# ==============================================================================
STATIC_URL = '/static/'
STATICFILES_DIRS = [BASE_DIR / 'static']
STATIC_ROOT = BASE_DIR / 'staticfiles'  # Pasta onde os arquivos serão coletados em produção

MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'         # Pasta para upload de imagens e documentos

# ==============================================================================
# CONFIGURAÇÃO DE E-MAIL (Configurado para Console por padrão)
# ==============================================================================
# Em produção, para enviar e-mails de convite, configure um servidor SMTP real:
if DEBUG:
    # Desenvolvimento: exibe os e-mails no terminal
    EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'
else:
    # Produção: Use as variáveis abaixo no seu arquivo .env
    # EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
    # EMAIL_HOST = os.getenv('EMAIL_HOST', 'smtp.gmail.com')
    # EMAIL_PORT = int(os.getenv('EMAIL_PORT', 587))
    # EMAIL_USE_TLS = os.getenv('EMAIL_USE_TLS', 'True') == 'True'
    # EMAIL_HOST_USER = os.getenv('EMAIL_HOST_USER', '')
    # EMAIL_HOST_PASSWORD = os.getenv('EMAIL_HOST_PASSWORD', '')
    pass

DEFAULT_FROM_EMAIL = os.getenv('DEFAULT_FROM_EMAIL', 'noreply@reabitech.com')

# ==============================================================================
# CONFIGURAÇÕES DE SEGURANÇA PARA PRODUÇÃO
# ==============================================================================
if not DEBUG:
    # Força redirecionamento para HTTPS em produção
    SECURE_SSL_REDIRECT = True
    
    # Os cookies de sessão e CSRF só serão enviados via HTTPS
    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_SECURE = True
    
    # HSTS (HTTP Strict Transport Security) - Garante que o navegador só use HTTPS
    SECURE_HSTS_SECONDS = 31536000  # 1 ano
    SECURE_HSTS_INCLUDE_SUBDOMAINS = True
    SECURE_HSTS_PRELOAD = True
    
    # Proteção contra clickjacking
    X_FRAME_OPTIONS = 'DENY'

# ==============================================================================
# CAMPO DE ID PADRÃO
# ==============================================================================
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# ==============================================================================
# UTILITÁRIOS DE DESENVOLVIMENTO
# ==============================================================================
# INTERNAL_IPS permite que ferramentas como django-debug-toolbar funcionem
INTERNAL_IPS = [
    '127.0.0.1',
]