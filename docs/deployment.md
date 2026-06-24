# 배포 계획 — AWS EC2 + GitHub Actions CI/CD

> 로컬 개발 완료 → **AWS EC2 단일 인스턴스에 docker-compose로 배포**하고,
> **GitHub Actions로 CI(테스트)·CD(자동 배포)** 를 구축한다.
> 상태: **Phase 1·2 완료(https://beautalk.site 운영 중), Phase 3(Actions) 진행 중 — 워크플로우
> 작성·푸시 완료, 첫 자동배포 디버깅 중**. 도메인: `beautalk.site`

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
- [x] EC2 생성 (Ubuntu 24.04 LTS, **t3.micro**, §4 결정), 보안그룹 22(SSH, My IP)/80/443(0.0.0.0/0)
  — AMI 검색 시 "SQL Server" 등 Marketplace 번들과 헷갈리지 않게 Quick Start 탭의 순정 Ubuntu만 선택
- [x] Docker + compose 플러그인 설치 (공식 apt 저장소, `docker-ce`·`docker-compose-plugin`)
- [x] 스왑 2GB + `vm.swappiness=10` (§5)
- [x] 도메인 A레코드(GoDaddy) → EC2 퍼블릭 IP — `www`는 기존 `@` CNAME이 따라가서 별도 레코드 불필요
- [x] 배포 브랜치에 `develop` 병합 — FE 작업(API base env화 등)과 백엔드 배포 작업이 서로 다른
  파일만 건드려 무충돌 병합. FE가 동일 브랜치에 이어서 푸시할 수 있도록 먼저 정리.
- [x] 서버에 프로덕션 env 주입 (시크릿) — **루트 `.env`**(DB_NAME/DB_USER/DB_PASSWORD, compose
  변수치환용) **+ `backend/.env`**(Django 전체 시크릿) **2개 모두**, `DB_*` 값 동일하게,
  `SECRET_KEY`·DB 비밀번호는 운영용으로 새로 생성(dev 값 재사용 안 함)
- [x] `docker compose up -d --build` → `migrate` → `loaddata`(products·board seed) →
  `backfill_form --apply` → `backfill_embeddings` — **데이터 트러블슈팅 발견**, 아래 참고
- [x] certbot으로 HTTPS 발급 — 아래 "HTTPS 발급 + OAuth 트러블슈팅" 참고
- [x] 카카오/구글 콘솔에 배포 redirect URI 등록 — 카카오 `KOE006` 함정, 아래 참고
- [x] 수동 E2E 검증: 로그인 → 추천 → 게시판 — 전 구간 통과, 아래 "E2E 검증 결과" 참고

#### 프로덕션 데이터 적재 트러블슈팅 — "체크리스트에 있다고 다 끝난 게 아니다"

**발견** — `loaddata products_seed.json`을 돌렸더니 "156 object(s) installed"가 나왔다. 로컬
dev DB는 306건(데이터 정제·임베딩·제형 백필 완료 상태)인데
정확히 절반밖에 안 들어간 게 이상해서 `git log -- backend/products_seed.json`을 봤더니, 이 픽스처는
**PostgreSQL 전환 커밋(초기 156건) 이후 단 한 번도 갱신된 적이 없었다.** 그 사이 진행한 크롤링
확장·중복 53건 제거·`form` 백필·임베딩 백필이 전부 빠진 스냅샷을 그대로 운영 DB에 넣고 있었던 것.
체크리스트엔 "loaddata"라고만 적혀 있어 무심코 지나치기 쉬운 함정이었다.

**왜 위험했나** — 하이브리드 추천(SQL `form` 필터 + 임베딩 RAG)은 두 필드가 비어 있으면 그냥
안 도는 게 아니라 **모든 후보가 필터에서 걸러져 추천 자체가 텅 비거나, 의미 검색이 무작위 폴백으로
빠지는** 식으로 조용히 망가진다. 에러 없이 "그냥 품질이 이상한" 상태라 발표 중에야 들킬 수 있었다.

**해결 — 두 단계 함정**
1. `python manage.py dumpdata products.Product --output products_seed.json`을 Windows에서
   돌리면 `cp949 codec can't encode` 에러가 난다(콘솔 코드페이지가 UTF-8이 아님). `PYTHONUTF8=1`
   환경변수로 강제 UTF-8 런타임 모드를 켜야 한글 제품명이 깨지지 않고 써진다.
2. 새 픽스처를 EC2 **호스트**의 `~/beautalk/backend/products_seed.json`에 올려도 `loaddata`가
   여전히 옛 156건을 읽었다. 원인: `docker-compose.prod.yml`의 backend는 **코드를 빌드 시점에
   이미지에 baked-in**(Dockerfile `COPY . .`)하고 호스트 디렉터리를 마운트하지 않으므로, 컨테이너
   안의 `/app/products_seed.json`은 이미지를 만들 때의 스냅샷이다. 호스트 파일을 바꿔도 이미 떠 있는
   컨테이너에는 반영되지 않는다 — `docker compose cp backend/products_seed.json
   backend:/app/products_seed.json`로 실행 중인 컨테이너에 직접 집어넣어야 한다(재빌드보다 빠름).
3. 갱신 전 156건이 모두 새 306건의 부분집합이 아닐 수 있어(중복 제거로 빠진 행), 그냥 `loaddata`만
   하면 사라져야 할 옛 행이 잔류한다 → `Product.objects.all().delete()`로 비우고서 재적재.
   `board.Post.products` M2M은 모델 설계상 "제품이 삭제되면 태그 행만 사라지고 글은 남는다"라
   안전하게 cascade됨(실제로 데모 게시글 하나가 가리키던, 중복 제거로 이미 없어진 제품 UUID 태그가
   조용히 빠짐 — 글 자체는 그대로).

**교훈** — git에 커밋된 픽스처(seed/fixture)는 "한 번 만들고 끝"이 아니라 데이터가 바뀌면 같이
갱신해야 하는 **코드와 동급의 자산**이다. Phase 3(Actions CD)에서는 이 적재 단계를 자동화하기
전에, 픽스처 자체가 최신인지 확인하는 절차(또는 매 배포마다 갱신하는 스크립트)를 넣어야 한다.

#### HTTPS 발급 + OAuth 트러블슈팅

**certbot** — nginx를 80포트로 먼저 띄워 ACME HTTP-01 챌린지 경로(`/.well-known/acme-challenge/`,
`docker-compose.prod.yml`의 `certbot/www` 볼륨)가 응답하는 걸 확인한 뒤, 별도 컨테이너로 1회성
발급을 실행했다(`docker run --rm -v ...certbot/conf:/etc/letsencrypt -v ...certbot/www:/var/www/certbot
certbot/certbot certonly --webroot -w /var/www/certbot -d beautalk.site -d www.beautalk.site`).
nginx 자체에 certbot을 심지 않고 별도 1회 실행으로 분리한 이유: 발급은 도메인당 1회면 되고, 갱신은
나중에 cron/systemd timer로 같은 명령을 재실행하면 되므로 nginx 컨테이너 수명과 묶을 필요가 없다.
발급 후 `nginx.conf`를 다시 써서 ① 80은 ACME 챌린지 통과 + 나머지는 443으로 301 리다이렉트만,
② 443 server 블록에 `ssl_certificate`/`ssl_certificate_key`로 `/etc/letsencrypt/live/beautalk.site/`
경로를 지정(이 경로는 certbot이 쓴 볼륨을 nginx 컨테이너도 마운트하고 있어 별도 복사 불필요).
`nginx -t`로 문법 검증 후 `restart`. 인증서는 Let's Encrypt, 2026-09-22 만료.

**카카오 `KOE006`(앱 관리자 설정 오류)** — 카카오 개발자 콘솔에 Redirect URI를 등록하고 로그인을
시도하니 카카오 쪽에서 일반적인 "앱 관리자 설정 오류" 화면이 떴다(우리 서버까지 요청이 오지도
못하고 카카오 단계에서 막힘 — nginx/backend 로그에 콜백 자체가 안 찍히는 것으로 확인). 원인은
사소했다: 등록한 Redirect URI가 `http://beautalk.site/...`로, **`s`가 빠진 오타**였다(코드는
`BACKEND_URL=https://beautalk.site`라 실제 보내는 redirect_uri는 https인데, 카카오 콘솔엔 http로
등록되어 있어 불일치). `https://`로 정정하자 즉시 정상 동작. 구글 콘솔은 처음부터 정확히 등록해
한 번에 통과. **교훈**: OAuth 제공자가 주는 에러 메시지(`KOE006`)는 일반적이라 redirect_uri
**문자열 단위(스킴까지)** 로 직접 대조하는 게 제일 빠른 디버깅이었다.

#### E2E 검증 결과

브라우저로 직접 진행하면서 서버 로그(`docker compose logs -f backend nginx`)를 실시간으로 같이
보는 방식으로 검증했다(에러가 나면 어느 요청에서 났는지 바로 대조 가능). 결과:
- 구글 로그인 → 콜백 → 토큰 교환 → 신규 유저 온보딩 → 프로필 생성(201)
- 카카오 로그인(redirect_uri 수정 후) → 동일 플로우로 온보딩 → 프로필 생성(201)
- 챗봇 대화(`POST /api/v1/chat/` 200 연속) → 추천 생성(`POST /api/v1/recommend/` 201)
- 추천 제품 찜(`POST /api/v1/likes/` 201)
- 커뮤니티: 목록(`GET /api/v1/posts/` 200) → 글 작성(`POST /api/v1/posts/` 201) → 상세(200) →
  제품 역참조(`GET /api/v1/products/{id}/posts/` 200) → 게시글 좋아요(`POST /api/v1/likes/` 201)

전 구간 에러 없이 통과. (참고: 로그 중간에 `GET /api/v1/auth/exchange/`가 한 번 401을 반환한
줄이 있는데, exchange 엔드포인트는 1회용 토큰을 소비하는 구조라 동일 콜백에서 중복 호출되면
두 번째는 401이 나는 게 정상 — 첫 호출이 이미 성공해 로그인 자체엔 영향 없음.)

### Phase 3 — GitHub Actions (진행 중 — 워크플로우 작성·푸시 완료, 첫 배포 디버깅 중)
- [x] **워크플로우 작성**: `.github/workflows/ci-cd.yml` — `test`(항상) → `deploy`(develop push + test 통과 시)
  통합 파이프라인. 배포 트리거 브랜치 = **develop**(결정, §4)
- [x] **CI(test 잡)**: develop으로의 PR·push마다 Django 테스트. pgvector service 컨테이너
  (`pgvector/pgvector:pg16` — 임베딩 `VectorExtension` 마이그레이션이 `CREATE EXTENSION vector`를
  요구), `DJANGO_DEBUG=True`로 throttle 끄고 DB_*는 service 컨테이너로 주입
- [x] **CD(deploy 잡)**: 프론트는 **Actions 러너에서 빌드**(t3.micro OOM 회피, §5) → dist tarball
  scp → EC2에서 `git fetch + reset --hard origin/develop` → dist 교체 → `docker compose up -d --build`
  → `migrate`. SSH/SCP는 `appleboy/ssh-action`·`appleboy/scp-action` 사용
- [x] **Secrets 등록**: `EC2_HOST`(52.78.34.135)·`EC2_USER`(ubuntu)·`EC2_SSH_KEY`(.pem 전체)
- [x] **사전 준비**: EC2 저장소를 `46-...` 브랜치 → **develop으로 전환**(`git reset --hard origin/develop`,
  얕은 클론이라 `git remote set-branches origin "*"` + `fetch develop:refs/...` 선행 필요),
  CD가 sudo 없이 docker 실행 가능함을 새 SSH 세션에서 확인, `certbot/`을 `.gitignore`에 추가
- [ ] ⚠️ **첫 배포 미반영 — 디버깅 필요**: 워크플로우 커밋(`323d80a`) push 후 ~6분 모니터링했으나
  EC2 HEAD가 갱신 안 됨(컨테이너 재기동 흔적 없음) → `test` 또는 `deploy` 잡이 실패한 것으로 추정.
  **다음 세션: GitHub Actions 탭에서 어느 잡이 왜 실패했는지 확인**이 출발점. 유력 후보:
  ① CI 테스트가 CI 환경(DEBUG=True)에서 깨짐(로컬은 DEBUG 미설정=False로 통과했었음 → throttle 등
  환경차 가능성), ② `EC2_SSH_KEY` 시크릿 개행 누락 등으로 appleboy 인증 실패, ③ Actions 미트리거.

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

- [x] **도메인 이름**: `beautalk.site` (GoDaddy 구매, A레코드 연결 완료)
- [x] **배포 브랜치**: **`develop` 직접 배포**(결정 2026-06-24) — 학교 프로젝트·데모 특성상 별도
  `main` 운용보다 단순함 우선. develop push/merge 시 자동 배포
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
