from pathlib import Path

# -------------------------------
# Paths
# -------------------------------
BASE_DIR = Path(__file__).resolve().parent.parent

# -------------------------------
# Seguridad
# -------------------------------
SECRET_KEY = 'django-insecure-m8-w3o7!zb1_#+rf)80vk0=h95(60_ztv7gya0#lb7$1bmla1g'

DEBUG = True
ALLOWED_HOSTS = []

# -------------------------------
# Aplicaciones
# -------------------------------
INSTALLED_APPS = [
    'jazzmin',
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',

    # Terceros
    'rest_framework',
    'corsheaders',

    # App principal
    'api.apps.ApiConfig',
]

# -------------------------------
# Middleware
# -------------------------------
MIDDLEWARE = [
    'corsheaders.middleware.CorsMiddleware', 
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

# -------------------------------
# Configuración CORS
# -------------------------------
CORS_ALLOWED_ORIGINS = [
    "http://127.0.0.1:52591",
    "http://127.0.0.1:5500",
    "http://127.0.0.1:5501",
    "http://localhost:5500",
    "http://localhost:5501",
]


CORS_ALLOW_ALL_ORIGINS = True


CORS_ALLOW_CREDENTIALS = True

# -------------------------------
# URLs
# -------------------------------
ROOT_URLCONF = 'backend.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'backend.wsgi.application'

# -------------------------------
# Base de datos
# -------------------------------
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }
}


# -------------------------------
# Validadores de contraseña
# -------------------------------
AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator'},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]

# -------------------------------
# Internacionalización
# -------------------------------
LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'UTC'
USE_I18N = True
USE_TZ = True

# -------------------------------
# Archivos estáticos
# -------------------------------
STATIC_URL = 'static/'

# -------------------------------
# Clave primaria por defecto
# -------------------------------
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'
JAZZMIN_SETTINGS = {
    "site_title": "Panel Administrativo - Brisa Caribeña",
    "site_header": "Administración del Sistema Brisa Caribeña",
    "site_brand": "Brisa Caribeña",
    "welcome_sign": "Bienvenido al panel administrativo",
    "copyright": "Brisa Caribeña © 2025",
    "show_ui_builder": True,
    "theme": "darkly", 
    "icons": {
        "api.Producto": "fas fa-utensils",
        "api.Pedido": "fas fa-receipt",
        "api.Mesa": "fas fa-chair",
        "api.Mesero": "fas fa-user-tie",
        "api.Pago": "fas fa-cash-register",
        "api.DetallePedido": "fas fa-list",
        "api.Categoria": "fas fa-tags",
    },
}

