# 배포 계획 — AWS EC2 + GitHub Actions CI/CD

> 로컬 개발 완료 → **AWS EC2 단일 인스턴스에 docker-compose로 배포**하고,
> **GitHub Actions로 CI(테스트)·CD(자동 배포)** 를 구축한다.
> 상태: **계획**. 관련 이슈: #(생성 시 부여) · 도메인: `<확정 필요>`

---

## 1. 아키텍처 (단일 EC2 + docker-compose)

```
              사용자 브라우저
                   │ HTTPS(443)
                   ▼
   ┌─────────── EC2 (Ubuntu) ───────────┐
   │  nginx (컨테이너)                     │
   │   ├─ /       → Vue 빌드 정적(dist/)   │   프론트 = 정적 파일 (별도 서버 X)
   │   └─ /api/   → 프록시 → backend:8000  │
   │  backend (컨테이너): gunicorn+Django  │
   │  db (컨테이너): postgres + pgvector   │   기존 docker-compose 확장
   └──────────────────────────────────────┘
            │
   외부: GMS API(LLM·임베딩) · 카카오/구글 OAuth
```

- **컨테이너 3개**: nginx · backend · db. 프론트는 빌드 산출물(정적), **Selenium 크롤링은 배포 제외**(로컬 데이터 작업 전용).
- **DB**: EC2 내 컨테이너 권장(공짜·기존 구성 재사용). RDS는 비용+pgvector 설정 추가.

---

## 2. 작업 단계 (수동 먼저 → 자동화 나중)

> ⚠️ **원칙**: Phase 2(수동 배포)를 한 번 성공시킨 뒤 그걸 Actions로 옮긴다.
> 처음부터 Actions로 가면 배포·CI 디버깅이 겹쳐 지옥이 된다.

### Phase 1 — 코드를 '배포 가능' 상태로 (EC2 불필요, 로컬 검증)
- [x] 백엔드 localhost 하드코딩 → env화 (`FRONTEND_URL`·`BACKEND_URL`·CORS·CSRF, §3)
- [x] `SECURE_PROXY_SSL_HEADER` + secure 쿠키 (nginx 뒤 HTTPS 인식)
- [x] `requirements.txt`에 `gunicorn`·`whitenoise` 추가
- [x] `backend/Dockerfile` (collectstatic + gunicorn)
- [x] `nginx/nginx.conf` (정적 서빙 + `/api`·`/admin`·`/static` 프록시)
- [x] `docker-compose.prod.yml` (db 튜닝 + backend + nginx, mem_limit)
- [x] `backend/.env.prod.example` (프로덕션 env 템플릿)
- [x] **회귀 테스트** — `python manage.py test` 63개 전부 통과 (env 기본값 localhost라 정상)
- [x] **로컬 prod compose 기동 검증** — 아래 "로컬 검증 트러블슈팅" 참고
- [ ] **프론트 API base env화 (FE 담당)** → 아래 spec

#### 로컬 검증 트러블슈팅 — "EC2 가기 전에 로컬에서 한 번 더 걸러낸다"

**왜 로컬에서 먼저 띄워봤나** — t3.micro는 프리티어 소진이라 인스턴스를 켜두는 시간도 비용이고,
EC2 위에서 디버깅하면 SSH·보안그룹·네트워크까지 변수가 겹쳐 원인 분리가 느려진다. 그래서 Phase 2(EC2)로
가기 전에 **같은 `docker-compose.prod.yml`을 로컬에서 그대로 띄워**, 인프라 설정 자체의 결함을
먼저 걸러내기로 했다(§2 원칙 — "수동 배포를 한 번 성공시킨 뒤 Actions로"의 연장선).

**검증 방법** — 프론트 `npm run build`로 `dist/` 생성 → `docker compose -f docker-compose.prod.yml
up -d --build`로 nginx·backend·db 동시 기동 → `curl`로 `/`(SPA index.html, 200) ·
`/api/v1/products/`(인증 필요 401 = 정상) · `/admin/`(302) · `/static/...`(whitenoise, 200) 확인 →
`migrate` 정상 동작 확인.

**발견한 버그** — 기동 로그에 `DB_USER`/`DB_NAME`/`DB_PASSWORD` "변수 미설정, 빈 문자열로 대체" 경고가
떴다. 원인을 추적해보니 `docker-compose.prod.yml`의 `db` 서비스가 `environment: POSTGRES_DB: ${DB_NAME}`
식으로 **컴포즈 파일 자체의 변수치환(interpolation)** 을 쓰는데, 이 치환은 **컴포즈 파일과 같은
디렉터리의 `.env`**(즉 루트 `.env`)에서만 일어난다. 반면 `backend/.env`는 `env_file:` 지시자로
**backend 컨테이너 내부 런타임 환경변수**로만 주입될 뿐, 컴포즈 YAML의 `${...}` 치환에는 전혀
관여하지 않는다 — 둘은 완전히 다른 메커니즘인데 이름이 비슷해 헷갈리기 쉬웠다.

**왜 위험했나** — 로컬에서는 기존 dev 작업 중 만들어둔 Postgres 볼륨이 이미 `beautalk`/`beautalk`
계정으로 초기화돼 있어서 우연히 동작한 것뿐이었다. 하지만 EC2는 **빈 볼륨에서 시작**하므로, 첫 `up`
시점에 Postgres 공식 이미지가 `POSTGRES_USER`/`POSTGRES_PASSWORD`를 빈 문자열로 받아 엉뚱한
자격증명(또는 초기화 자체 실패)으로 DB를 만들고, 이후 `backend`는 `backend/.env`의 실제
`DB_USER=beautalk`로 접속을 시도해 인증 실패 → **배포 첫 단계부터 컨테이너가 죽는** 상황이 됐을 것이다.
로컬 검증이 없었다면 이 문제는 EC2에서야, 그것도 "왜 DB 연결이 안 되지"라는 훨씬 알기 어려운
증상으로 드러났을 것.

**해결** — 루트에 `.env.prod.example`을 새로 추가해 "이 값들은 compose 변수치환용으로 루트에 둬야
한다"는 걸 명시했고, `docker-compose.prod.yml` 상단 주석에 **env 파일이 2개(루트 `.env` + `backend/.env`)
필요하며 `DB_*` 값을 반드시 맞춰야 한다**고 적었다. `.gitignore`에 `!.env.prod.example` 예외를 추가해
두 example 파일(`루트`·`backend`)이 git에 잡히도록 했다(기존엔 `.env.*` 패턴에 걸려 안 보였음).

**교훈** — `env_file:`(컨테이너 런타임 주입)과 `${VAR}`(컴포즈 YAML 치환)는 같은 "`.env`"란 단어를
쓰지만 읽는 위치와 시점이 다르다. docker-compose로 여러 env 파일을 쓸 때는 "이 변수가 언제, 어디서
읽히는가"를 서비스별로 명확히 구분해 문서화해야 같은 실수가 재발하지 않는다.

#### 프론트엔드 변경 spec (FE 팀원에게)
API 주소가 여러 파일에 `http://localhost:8000/api/v1`로 하드코딩됨 → **env로 중앙화** 필요:
- `services/api.js`: `const BASE_URL = import.meta.env.VITE_API_BASE || 'http://localhost:8000/api/v1'`
- 하드코딩 직접 호출도 같은 base로 교체:
  - `App.vue`(token/refresh), `views/AuthCallbackView.vue`(exchange),
    `views/LoginView.vue`(kakao/google login), `stores/auth.js`(logout)
- `frontend/.env.production`: `VITE_API_BASE=https://beautalk.site/api/v1`
- 빌드: `npm run build` → `frontend/dist/` (이걸 nginx가 서빙. **빌드는 Actions에서**, EC2 X)

### Phase 2 — EC2 '수동' 1회 배포 (동작 검증)
- [ ] EC2 생성 (Ubuntu 24.04 LTS, **t3.micro**, §4 결정), 보안그룹 22/80/443
- [ ] Docker + compose 플러그인 설치
- [ ] 도메인 A레코드 → EC2 퍼블릭 IP
- [ ] 서버에 프로덕션 env 주입 (시크릿) — **루트 `.env`**(DB_NAME/DB_USER/DB_PASSWORD, compose
  변수치환용) **+ `backend/.env`**(Django 전체 시크릿) **2개 모두**, `DB_*` 값 동일하게
- [ ] `docker compose up -d` → `migrate` → `loaddata`(products·board seed) → `backfill_form --apply` → `backfill_embeddings`
- [ ] certbot으로 HTTPS 발급
- [ ] 카카오/구글 콘솔에 배포 redirect URI 등록
- [ ] 수동 E2E 검증: 로그인 → 추천 → 게시판

### Phase 3 — GitHub Actions
- [ ] **CI**: PR/push에 Django 테스트 (PG service 컨테이너) + (선택) 프론트 빌드
- [ ] **CD**: 배포 브랜치 push → SSH로 EC2 접속 → `git pull` + `docker compose up -d --build` + `migrate`
- [ ] Secrets: `EC2_HOST`, `EC2_SSH_KEY`, `EC2_USER` 등

---

## 3. 배포 전 코드 변경 — 하드코딩 → env

| 위치 | 현재 | 변경 |
|------|------|------|
| `accounts/views.py` | OAuth `redirect_uri` = `http://localhost:8000/...` | 배포 도메인 (env `OAUTH_REDIRECT_BASE` 등) |
| `accounts/views.py` | 콜백 후 프론트 리다이렉트 `http://localhost:5173/...` | 배포 도메인 (env `FRONTEND_URL`) |
| `config/settings.py` | `CORS_ALLOWED_ORIGINS = ['http://localhost:5173']` | env로 배포 도메인 |
| `frontend` | API base URL = localhost:8000 | 빌드 시 `VITE_API_BASE` = 배포 도메인 |
| `.env` | — | `DJANGO_DEBUG=False`, `DJANGO_ALLOWED_HOSTS=도메인` (코드는 준비됨) |

> 카카오/구글 **개발자 콘솔에도** 배포 redirect URI를 등록해야 OAuth가 통과한다(HTTPS 필수).

---

## 4. 결정 사항 (확정 필요)

- [ ] **도메인 이름**: `beautalk.site`
- [ ] **배포 브랜치**: `main`(배포 전용, 권장) vs `develop`
- [x] **DB**: 컨테이너 (RDS 안 씀)
- [x] **EC2 사양**: **t3.micro (1GB)** — 프리티어 소진, 최소비용. 1GB 최적화는 §5.

---

## 5. t3.micro (1GB) 최적화 플랜

t3.micro(1GB RAM·2vCPU·~$9.5/월). 1GB는 빡빡하므로 **스왑 + 빌드 오프로드 + 메모리 튜닝**으로 잡는다.

### 메모리 예산 (1GB + 스왑 2GB)
| 구성 | 대략 |
|------|------|
| OS(Ubuntu) | ~200MB |
| postgres (튜닝) | ~150MB |
| gunicorn 2 workers | ~350MB |
| nginx | ~20MB |
| Docker daemon | ~80MB |
| **합** | **~800MB** (+ 스왑 버퍼) |

### 핵심 최적화 7
1. **스왑 2GB (필수)** — OOM 방지
   ```bash
   sudo fallocate -l 2G /swapfile && sudo chmod 600 /swapfile
   sudo mkswap /swapfile && sudo swapon /swapfile
   echo '/swapfile none swap sw 0 0' | sudo tee -a /etc/fstab
   ```
2. **프론트 빌드는 EC2에서 절대 안 함** — GitHub Actions에서 빌드 → `dist/`만 배포 (node 빌드가 1GB+ 먹어 OOM 주범)
3. **백엔드 이미지도 Actions 빌드 → GHCR push → EC2는 pull만** (Phase 3). Phase 2 수동 빌드는 스왑으로 버팀
4. **gunicorn `--workers 2 --timeout 120 --max-requests 500`** — LLM 호출 길어 timeout 넉넉히, max-requests로 워커 주기적 재생성(메모리 누수 방지)
5. **PostgreSQL 튜닝** — `shared_buffers=128MB`, `max_connections=20`, `work_mem` 작게 (데이터 ~300건이라 충분)
6. **compose `mem_limit`** — db 256m / backend 450m / nginx 64m (한 서비스 폭주 차단)
7. **`vm.swappiness=10`** — 스왑 남용 방지

### 비용
t3.micro ~$9.5/월 + EBS 30GB(거의 무료) → 실질 **~1만원/월**. 발표 끝나면 인스턴스 삭제 → 과금 종료.
