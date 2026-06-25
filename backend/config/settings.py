from pathlib import Path
from datetime import timedelta
import os
from dotenv import load_dotenv

load_dotenv()

BASE_DIR = Path(__file__).resolve().parent.parent

SECRET_KEY = os.environ.get('DJANGO_SECRET_KEY')

# 배포 시 트레이스백 노출 방지. 안전을 위해 기본값을 False로 둔다(미설정=운영 안전).
# 로컬 개발자는 .env 에 DJANGO_DEBUG=True 를 명시해서 켠다 (fail-safe 기본값).
DEBUG = os.environ.get('DJANGO_DEBUG', 'False').lower() == 'true'

# DEBUG=False가 되는 순간 ALLOWED_HOSTS가 비면 전 요청이 400이 되므로
# 로컬 기본값을 제공하고, 운영 도메인은 .env(DJANGO_ALLOWED_HOSTS=도메인,IP)로 주입.
ALLOWED_HOSTS = os.environ.get('DJANGO_ALLOWED_HOSTS', 'localhost,127.0.0.1').split(',')


INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'rest_framework',
    'rest_framework_simplejwt.token_blacklist',
    'corsheaders',
    'accounts',
    'products',
    'chat',
    'board',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',   # 정적 파일(admin·DRF) 서빙
    'corsheaders.middleware.CorsMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

# 로컬 기본값 + 배포 도메인(env, 콤마 구분). 프론트·API가 같은 도메인이면 CORS는 사실상
# 불필요하나, 로컬 dev(5173↔8000)와 분리 배포 대비해 env로 허용 오리진을 받는다.
CORS_ALLOWED_ORIGINS = [
    o.strip() for o in os.environ.get(
        'CORS_ALLOWED_ORIGINS', 'http://localhost:5173'
    ).split(',') if o.strip()
]
CORS_ALLOW_CREDENTIALS = True

# 운영(HTTPS) 세션·admin POST를 위한 신뢰 오리진. env로 배포 도메인 주입.
CSRF_TRUSTED_ORIGINS = [
    o.strip() for o in os.environ.get('CSRF_TRUSTED_ORIGINS', '').split(',') if o.strip()
]

# nginx가 SSL 종료 후 HTTP로 프록시하므로, 이 헤더로 Django가 원요청을 HTTPS로 인식하게 한다
# (없으면 secure 쿠키 미설정·리다이렉트 깨짐).
SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')
SESSION_COOKIE_SECURE = not DEBUG
CSRF_COOKIE_SECURE = not DEBUG

REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': [
        'rest_framework_simplejwt.authentication.JWTAuthentication',
    ],
    'DEFAULT_PAGINATION_CLASS': 'rest_framework.pagination.PageNumberPagination',
    'PAGE_SIZE': 10,
    'DEFAULT_THROTTLE_CLASSES': (
        [] if DEBUG else [
            'rest_framework.throttling.AnonRateThrottle',
            'rest_framework.throttling.UserRateThrottle',
        ]
    ),
    'DEFAULT_THROTTLE_RATES': {
        'anon': '20/hour',
        'user': '100/day',
        # LLM(유료 GMS) 호출 한도. 빈도 특성이 달라 분리한다:
        #  - chat: 한 상담에 메시지가 여러 개 오가므로 넉넉히
        #  - recommend: 배치 생성이라 호출이 드물고 프롬프트가 무거우므로 빡빡하게
        # DEBUG에선 None으로 비활성화(rate=None이면 throttle 통과 → 로컬·테스트 보호).
        'chat': None if DEBUG else '100/day',
        'recommend': None if DEBUG else '20/day',
    },
}

SIMPLE_JWT = {
    'ACCESS_TOKEN_LIFETIME': timedelta(minutes=30),
    'REFRESH_TOKEN_LIFETIME': timedelta(days=7),
    'ROTATE_REFRESH_TOKENS': True,
    'BLACKLIST_AFTER_ROTATION': True,
    'AUTH_HEADER_TYPES': ('Bearer',),
}

ROOT_URLCONF = 'config.urls'

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

WSGI_APPLICATION = 'config.wsgi.application'


# PostgreSQL 전용. pgvector(임베딩)·ArrayField(form) 등 PG 기능에 의존하므로
# SQLite 폴백은 두지 않는다. 접속정보는 .env 의 DB_* 값으로 주입한다.
DATABASES = {
    'default': {
        'ENGINE': os.environ.get('DB_ENGINE', 'django.db.backends.postgresql'),
        'NAME': os.environ.get('DB_NAME'),
        'USER': os.environ.get('DB_USER'),
        'PASSWORD': os.environ.get('DB_PASSWORD'),
        'HOST': os.environ.get('DB_HOST'),
        'PORT': os.environ.get('DB_PORT'),
    }
}


AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator'},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]


LANGUAGE_CODE = 'ko-kr'
TIME_ZONE = 'Asia/Seoul'
USE_I18N = True
USE_TZ = True

STATIC_URL = 'static/'
# collectstatic 수집 경로 (whitenoise가 여기서 admin·DRF 정적을 서빙). 컨테이너 빌드 시 수집.
STATIC_ROOT = BASE_DIR / 'staticfiles'

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'
