# SQLite → PostgreSQL 전환

> 작업일: 2026-06-23
> 브랜치: `28-feat-db-postgresql-전환`
> 결과: ✅ 34개 테스트 전부 통과 · Product 156건 이관 완료 · 한글 무결성 확인

---

## 🎯 목적

배포 전 **동시성·데이터 안정성** 확보를 위해 개발/운영 DB를 PostgreSQL로 전환한다.
SQLite는 단일 파일·쓰기 잠금 한계로 동시 요청 처리에 취약하다.

> 💡 **개념 — SQLite vs PostgreSQL, 무엇이 다른가?**
>
> - **SQLite**는 "라이브러리형" DB다. 별도 서버 프로세스 없이 **하나의 파일(`db.sqlite3`)**을 직접 읽고 쓴다. 설정이 필요 없어 개발 초기엔 최고지만, 쓰기 작업이 일어나면 **파일 전체에 잠금(lock)**이 걸린다. 즉 한 명이 글을 쓰는 동안 다른 요청은 기다려야 한다 → 사용자가 늘면 병목.
> - **PostgreSQL**은 "클라이언트-서버형" DB다. **독립된 DB 서버 프로세스**가 떠 있고, 앱(Django)이 네트워크로 접속한다. **MVCC**(다중 버전 동시성 제어) 덕분에 여러 사용자가 **동시에 읽고 쓰는 것**을 행(row) 단위로 처리한다 → 동시성에 강하다.
> - 한 줄 요약: *"혼자 쓰는 메모장(SQLite)" → "여러 명이 동시에 접속하는 도서관 사서(PostgreSQL)"*로 바꾸는 작업.

### 방향 결정 — 로컬 설치 대신 Docker

| 선택지 | 비고 |
|--------|------|
| 로컬 PostgreSQL 직접 설치 | 환경 오염, 배포 환경과 불일치 |
| **Docker 컨테이너** ✅ | 향후 전체 컨테이너화로 자연 확장, 개발=운영 환경 일치 |

배포 단계에서 어차피 컨테이너화가 예정되어 있어, 지금부터 PostgreSQL을 컨테이너로 띄우면
이후 백엔드 서비스만 `docker-compose`에 얹으면 된다.

> 💡 **개념 — 컨테이너(Docker)란?**
>
> 컨테이너는 *"실행에 필요한 모든 것(DB 엔진 + 설정 + 라이브러리)을 통째로 담은 표준 상자"*다.
> - **이미지(image)**: 상자의 설계도. 우리는 `postgres:16`이라는 공식 이미지를 가져다 쓴다 → PostgreSQL 16이 설치·설정된 환경을 1초 만에 재현.
> - **컨테이너(container)**: 그 설계도로 실제로 띄운 실행 인스턴스.
> - 왜 좋은가? **"내 PC에선 되는데요" 문제를 없앤다.** 내 노트북, 팀원 PC, 운영 서버 모두 같은 이미지로 띄우면 **완전히 동일한 DB 환경**이 보장된다. 로컬에 PostgreSQL을 직접 설치하면 버전·인코딩·경로가 사람마다 제각각이 되지만, 컨테이너는 그 차이를 원천 봉쇄한다.
> - 그래서 "개발 = 운영 환경 일치"가 가능하고, 나중에 백엔드 앱까지 컨테이너로 묶으면 배포가 `docker compose up` 한 줄로 끝난다.

---

## 🗂️ 변경 파일

| 파일 | 변경 내용 |
|------|-----------|
| `docker-compose.yml` 🆕 | PostgreSQL 16 컨테이너 (UTF-8 인코딩 고정, healthcheck, 데이터 볼륨) |
| `backend/config/settings.py` | DATABASES 환경변수화 (`DB_ENGINE` 미설정 시 SQLite 폴백) |
| `backend/requirements.txt` | `psycopg2-binary==2.9.10` 추가 |
| `backend/products/models.py` | `URLField` `max_length` 200 → 500 확장 |
| `backend/products/migrations/0005_…` 🆕 | URLField 길이 변경 마이그레이션 |
| `backend/chat/tests.py` | GMS mock 검증을 `data=` 전송 방식에 맞게 수정 |
| `backend/products_seed.json` 🆕 | Product 156건 시드 (loaddata용) |
| `backend/.env` (커밋 제외) | DB 접속정보 6종 추가 |

---

## ⚙️ 핵심 설정

### docker-compose.yml

```yaml
services:
  db:
    image: postgres:16
    container_name: beautalk-postgres
    restart: unless-stopped
    environment:
      POSTGRES_DB: ${DB_NAME:-beautalk}
      POSTGRES_USER: ${DB_USER:-beautalk}
      POSTGRES_PASSWORD: ${DB_PASSWORD:-beautalk}
      LANG: ko_KR.utf8
      POSTGRES_INITDB_ARGS: "--encoding=UTF8 --locale=C"
    ports:
      - "${DB_PORT:-5432}:5432"
    volumes:
      - postgres_data:/var/lib/postgresql/data
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U ${DB_USER:-beautalk} -d ${DB_NAME:-beautalk}"]
      interval: 5s
      timeout: 5s
      retries: 5

volumes:
  postgres_data:
```

> 💡 **개념 — compose 설정 한 줄씩 왜 넣었나?**
>
> - `image: postgres:16` — 버전을 **명시 고정**. `latest`를 쓰면 어느 날 17로 올라가 호환성 사고가 날 수 있어 위험.
> - `environment` — 컨테이너가 처음 켜질 때 **DB/계정/비밀번호를 자동 생성**. `${DB_NAME:-beautalk}`는 *"환경변수가 있으면 그 값, 없으면 기본값 beautalk"* → 설정 없이도 바로 동작.
> - `POSTGRES_INITDB_ARGS: "--encoding=UTF8"` — DB를 **UTF-8로 초기화**. 한글 데이터가 깨지지 않도록 처음부터 못 박는다. (이게 없으면 OS 로캘에 따라 인코딩이 달라질 수 있음)
> - `volumes: postgres_data` — **데이터 영속성**. 컨테이너는 원래 *"끄면 내부 데이터가 날아가는"* 일회성이다. 볼륨은 DB 데이터를 컨테이너 바깥에 따로 저장해, `docker compose down` 후 다시 띄워도 **데이터가 유지**되게 한다.
> - `healthcheck` — *"DB가 진짜 접속 받을 준비가 됐는지"* 주기적으로 확인. 컨테이너가 "켜짐"과 "쿼리 받을 준비 완료"는 다르다. `pg_isready`로 준비 완료를 감지해야, 그 뒤 `migrate`가 안전하게 붙는다.

### settings.py (폴백 구조)

```python
# DB_ENGINE 미설정 시 SQLite로 폴백 (팀원 로컬 환경 보호).
DATABASES = {
    'default': {
        'ENGINE': os.environ.get('DB_ENGINE', 'django.db.backends.sqlite3'),
        'NAME': os.environ.get('DB_NAME', BASE_DIR / 'db.sqlite3'),
        'USER': os.environ.get('DB_USER', ''),
        'PASSWORD': os.environ.get('DB_PASSWORD', ''),
        'HOST': os.environ.get('DB_HOST', ''),
        'PORT': os.environ.get('DB_PORT', ''),
    }
}
```

> `.env` 없는 팀원은 그대로 SQLite로 동작 → 점진적 전환 가능.

> 💡 **개념 — 왜 설정을 코드가 아닌 환경변수로 빼는가? (12-Factor)**
>
> 접속정보(호스트·비밀번호 등)를 코드에 직접 박으면 두 가지 문제가 생긴다. ① 비밀번호가 **Git에 그대로 노출**되고, ② 개발/운영 환경마다 코드를 고쳐야 한다.
> - 해결책은 **"설정은 환경변수로, 코드는 그대로"**. 같은 코드가 `.env` 값만 바뀌면 로컬에선 localhost PG에, 운영에선 AWS RDS에 붙는다 → 코드 수정 0.
> - `os.environ.get('DB_ENGINE', 'sqlite3')`의 두 번째 인자가 **폴백(기본값)**이다. 이 한 줄 덕분에 *"PG 세팅을 안 한 팀원은 자동으로 기존 SQLite 사용"* → 전환 과정에서 **누구의 환경도 깨지지 않는다.** 한꺼번에 갈아엎지 않고 점진적으로 옮길 수 있는 안전장치.

### .env (예시)

```
DB_ENGINE=django.db.backends.postgresql
DB_NAME=beautalk
DB_USER=beautalk
DB_PASSWORD=beautalk
DB_HOST=localhost
DB_PORT=5432
```

---

## 🚀 실행 절차

```bash
# 0) (사전) SQLite가 살아있을 때 Product 덤프 — 한글 안전을 위해 -X utf8
python -X utf8 manage.py dumpdata products.Product --indent 2 -o products_seed.json

# 1) PostgreSQL 컨테이너 기동
docker compose up -d
docker compose ps          # health: healthy 확인

# 2) psycopg2 설치
pip install -r requirements.txt

# 3) 스키마 생성
python manage.py migrate
```

> 💡 **개념 — `psycopg2`는 왜 필요한가? (DB 드라이버)**
>
> Django는 PostgreSQL의 통신 규약(프로토콜)을 직접 알지 못한다. 그 사이에서 *"Django의 명령 → PostgreSQL이 알아듣는 말"*로 번역해주는 **통역사**가 필요한데, 그게 바로 **드라이버(어댑터)** `psycopg2`다. SQLite 드라이버는 파이썬에 기본 내장이라 따로 설치가 없었지만, PostgreSQL은 외부 패키지가 필요하다.
> - `psycopg2-binary`를 쓴 이유: 일반 `psycopg2`는 설치 시 C 컴파일러가 필요한데, `-binary` 버전은 **컴파일된 형태로 배포**되어 Windows에서도 바로 설치된다.

> 💡 **개념 — `migrate`가 하는 일**
>
> 새로 띄운 PostgreSQL은 **완전히 텅 빈 상태**다. `migrate`는 Django 모델 정의(`models.py`)와 마이그레이션 파일을 읽어, PG 안에 **테이블·컬럼·제약조건을 실제로 만든다.** 즉 "그릇(스키마)을 먼저 빚는" 단계. 이게 끝나야 데이터를 부을 수 있다.

```bash

# 4) Product 156건 적재
python -X utf8 manage.py loaddata products_seed.json

# 5) 검증
python manage.py test      # 34 passed
```

> **데이터 이관 범위**: Product만. (그 외 데이터는 사실상 없어 `dumpdata`/`loaddata` 한 방으로 충분)

> 💡 **개념 — `dumpdata` / `loaddata` (픽스처)란?**
>
> DB를 갈아탈 때 *"기존 데이터를 어떻게 옮기지?"*가 문제다. SQLite 파일을 그대로 복사할 순 없다(엔진이 다르니까). 그래서 Django는 **DB에 독립적인 중간 포맷(JSON)**으로 데이터를 빼냈다 넣는다.
> - `dumpdata` — DB 안의 데이터를 **JSON 텍스트로 추출**(직렬화). 엔진과 무관한 순수 데이터만 남으므로 SQLite든 PG든 상관없다. 이렇게 뽑은 JSON 파일을 **픽스처(fixture)**라 부른다.
> - `loaddata` — 그 JSON을 **새 DB에 다시 삽입**(역직렬화). 단, 받을 **테이블이 먼저 있어야** 하므로 반드시 `migrate` 다음에 실행한다.
> - 왜 `contenttypes`·`auth.permission`은 제외하나? 이 둘은 `migrate`가 **자동으로 재생성**하는 시스템 데이터다. 중복으로 넣으면 PK 충돌이 난다. (이번엔 Product만 떠서 해당 없음)
> - 순서가 핵심: **`migrate`(그릇) → `loaddata`(내용물)**. 반대로 하면 "테이블 없음" 에러.

---

## 🐛 트러블슈팅

### #1 — dumpdata 한글이 콘솔에서 깨져 보임 (데이터는 정상)

- **증상**: 덤프/조회 시 콘솔에 제품명이 `���̿�����`로 표시됨.
- **원인**: 파일이 아닌 **Windows 콘솔 출력 인코딩(cp949)** 문제. 파일·DB는 정상 UTF-8.
- **검증**: `decode('utf-8')` 성공 + 한글 범위 검사 `True` + 에디터로 `바이오힐보` 정상 확인.
- **교훈**: Windows 한글 파이프라인은 **콘솔 표시를 신뢰하지 말 것**. 파일 출력은 `python -X utf8`로 강제, 검증은 바이트 디코드로.

### #2 — loaddata 실패: `value too long for type character varying(200)`

- **증상**: PG에 Product 적재 시 첫 행부터 `DataError`.
- **원인**: `URLField`의 기본 `max_length=200`인데 올리브영 추적 URL이 **최대 298자**.
  **SQLite는 길이 제한을 무시하지만 PostgreSQL은 강제**한다 — 전형적 이행 함정.
- **해결**: `oliveyoung_url`·`image_url` → `max_length=500`. 마이그레이션 0005 생성·적용 후 재적재 → 156건 성공.
- **교훈**: SQLite에서 잘 돌던 모델도 PG 전환 시 `CharField`/`URLField` 길이를 **실데이터 기준**으로 재점검할 것.

> 💡 **개념 — 왜 SQLite에선 멀쩡했나? (동적 타입 vs 정적 타입)**
>
> 같은 `models.py`인데 SQLite에선 오류가 없다가 PG에서 터진 이유가 바로 두 DB의 성격 차이다.
> - **SQLite는 "동적 타입"** — 컬럼에 `VARCHAR(200)`이라 적어둬도 **그 길이를 강제하지 않는다.** 298자를 넣어도 그냥 받아준다(타입 선언을 권고사항처럼 취급). 그래서 문제가 **숨어 있었다.**
> - **PostgreSQL은 "정적 타입"** — `VARCHAR(200)`이면 **201자부터 거부**한다(엄격). 숨어 있던 길이 초과가 전환 순간 드러난 것.
> - 교훈을 일반화하면: *"SQLite에서 통과했다 ≠ 데이터가 스키마에 맞다."* PG 같은 엄격한 DB로 옮기는 순간 그동안 묵인됐던 위반이 한꺼번에 드러난다. → 전환은 **잠재 버그를 조기에 잡아주는 건강검진**이기도 하다.

```python
# 실데이터 최대 길이 측정
# oliveyoung_url max: 298  ← 200 초과 (원인)
# image_url max: 115
# name max: 66 / brand max: 6
oliveyoung_url = models.URLField(max_length=500)
image_url = models.URLField(max_length=500)
```

### #3 — 전환 후 테스트 3건 실패 (`KeyError: 'json'`)

- **증상**: `chat.tests`에서 `mock_post.call_args.kwargs['json']` KeyError.
- **원인**: PG와 무관. 앞선 UTF-8 수정에서 GMS 호출을 `json=` → `data=`(인코딩된 bytes)로 바꿨는데 테스트가 옛 방식을 검증.
- **해결**: `_sent_payload()` 헬퍼 추가 — `kwargs['data']`를 UTF-8 디코드·파싱. 3곳 교체 → 34 passed.
- **교훈**: 요청 전송 방식(`json=`/`data=`) 변경 시 **mock 검증 코드도 함께 갱신**.

```python
def _sent_payload(mock_post):
    """_call_gms가 GMS로 보낸 payload 복원 (data= bytes 디코드)."""
    data = mock_post.call_args.kwargs['data']
    if isinstance(data, (bytes, bytearray)):
        data = data.decode('utf-8')
    return json.loads(data)
```

### (참고) docker compose 시 데몬 미기동

- **증상**: `failed to connect to the docker API ... dockerDesktopLinuxEngine ... cannot find the file`.
- **원인**: Docker Desktop은 설치됐으나 **앱(엔진)이 실행 중이 아님**.
- **해결**: Docker Desktop 앱 실행 → 엔진 기동 후 재시도.

---

## 💡 커밋 메시지

```
feat: SQLite에서 PostgreSQL로 DB 전환

- docker-compose: PostgreSQL 16 컨테이너 (UTF-8 인코딩 고정, healthcheck)
- settings: DATABASES 환경변수화 (DB_ENGINE 미설정 시 SQLite 폴백)
- products: URLField max_length 200→500 (PG는 길이 강제, 올리브영 URL 최대 298자)
- chat/tests: GMS mock 검증을 data= 전송 방식에 맞게 수정
- Product 156건 시드(products_seed.json) 추가, loaddata로 이관
```

---

## 📌 후속 메모

- `products_seed.json` 레포 포함 여부 결정 필요 (팀원/CI가 `loaddata`로 재현 가능 → 포함 추천).
- 향후 배포 단계에서 `docker-compose.yml`에 **backend 서비스** 추가 → 전체 컨테이너화.
- 운영 시 `.env`의 `DB_PASSWORD`는 개발용(`beautalk`)이 아닌 강한 비밀번호로 교체.
