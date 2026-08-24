# Beautalk 백엔드 — Django + gunicorn.
# Selenium/크롤링은 배포 대상 아님(requirements.txt에 없음) → 이미지 가볍게 유지.
FROM python:3.11-slim

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1

WORKDIR /app

# 의존성 먼저 복사 → 레이어 캐시 활용 (psycopg2-binary는 휠 설치라 컴파일러 불필요)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 8000

# collectstatic은 런타임에(.env 주입된 뒤) 실행 — 빌드 시점엔 SECRET_KEY 등이 없으므로.
# migrate는 자동화하지 않고 배포 스크립트/수동으로 분리(예기치 못한 마이그레이션 방지).
# gunicorn: 워커 2, LLM 호출 대비 timeout 120, max-requests로 워커 주기 재생성(메모리 누수 방지).
CMD ["sh", "-c", "python manage.py collectstatic --noinput && gunicorn config.wsgi:application --bind 0.0.0.0:8000 --workers 2 --timeout 120 --max-requests 500"]
