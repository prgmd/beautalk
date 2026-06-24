# Beautalk — 진행 현황

---

## ✅ 완료

### 프로젝트 세팅
- [x] 레포지토리 생성 및 협업 환경 구성 (Collaborator, 브랜치 룰셋, PR 템플릿, gitignore)
- [x] README.md 초안 작성

### Django·Vue 초기화
- [x] Django 프로젝트 초기화 (config, 패키지 설치, settings.py 설정)
- [x] Vue 3 프로젝트 초기화 (Router, Pinia, ESLint, Prettier)
- [x] DB 초기화 (앱 구조 설계, 모델 작성, 마이그레이션)

### 기획 및 설계
- [x] 기획 문서 작성 (기능명세서 v1.0, 와이어프레임, 유스케이스 다이어그램)
- [x] ERD 설계 및 다이어그램 작성
- [x] API 명세서 작성 (Request Body, Response, Status Code 포함)

### 크롤링 스크립트
- [x] 크롤링 환경 구성 (robots.txt 확인, undetected_chromedriver 적용, 카테고리 4종)
- [x] 상품·리뷰 데이터 수집 및 DB 저장
- [x] Gemini API 연동 → ai_summary 및 타입별 만족도 생성

---

## 🔲 진행 예정

### OAuth
- [x] 카카오 OAuth 연동
- [x] 구글 OAuth 연동
- [x] JWT 토큰 발급 및 갱신 (SIMPLE_JWT 설정, Refresh 블랙리스트)
- [x] OAuth CSRF 방어 (state 파라미터)
- [x] OAuth 콜백 에러 처리 (code 누락, provider 에러, 토큰 교환 실패)
- [x] Vue 라우터 가드
- [x] JWT HttpOnly 쿠키 관리 (세션 교환 → access 바디 + refresh 쿠키)
- [x] 401 자동 갱신 (api.js 인터셉터)
- [x] 페이지 새로고침 시 토큰 복원 (startup refresh)
- [x] 온보딩 스킵 시 챗봇 진입 처리

### 온보딩 UI·API
- [x] 피부 타입 선택 UI (건성/지성/복합성/민감성)
- [x] 피부 고민 선택 UI (여드름/주름/색소침착/모공 등 다중 선택)
- [x] 기피 성분 입력 UI (알레르기/기피 성분 다중 선택)
- [x] 온보딩 데이터 백엔드 저장
- [x] 프로필 지정 → 챗봇 추천 자동 참조 연동

### 프로필 API·UI
- [x] Serializer 작성 (SkinProfileSerializer + JSONField 검증, UserInfoSerializer)
- [x] 프로필 조회/생성/수정 API (GET, POST, PATCH /api/v1/profile)
- [x] URL 연결 (accounts/urls.py, config/urls.py)
- [x] 로그아웃 (refresh 토큰 블랙리스트 + HttpOnly 쿠키 삭제)
- [x] 찜 API (GET/POST /api/v1/likes/, DELETE /api/v1/likes/{product_id}/, 제품정보 포함·IDOR 방어)
- [x] 제품 조회 API (GET /api/v1/products/, /api/v1/products/{id}/ — 페이지네이션·카테고리 필터)
- [x] 회원 탈퇴 API (DELETE /api/v1/account/ — 토큰 무효화 + CASCADE 삭제)
- [x] 마이페이지 UI (피부 프로필 확인 및 수정)
- [x] 찜한 제품 리스트 UI (백엔드 연동) 및 올리브영 링크 이동

### 챗봇 API (대화 → 추천 분리 아키텍처)
> 설계: [docs/chat-recommend-plan.md](./chat-recommend-plan.md) 참고
> - 대화 단계: 자연어만 주고받으며 추천에 필요한 정보 수집 (content/ready JSON)
> - 추천 단계: history 기반 배치 생성 (LLM이 제품 id 추출 → DB 검증 → 배치 저장)
> - 히스토리: 배치 단위 타임라인 (products = ProductSerializer 전체 + reason)
> - 토큰 효율: Phase 2에서 RAG 벡터 검색으로 개선 예정 (PostgreSQL 전환 완료 → pgvector 도입 기반 마련, plan.md 2-6)
>
> ⚠️ **기피 성분 필터는 이번 범위 제외** (제품 성분 데이터 부재, Phase 2)
- [x] 추천 배치 기록 모델 (Recommendation 부모 + RecommendedProduct 자식, 이벤트 로그)
- [x] 마이그레이션: chat/0002_recommendedproduct 생성·적용
- [x] 챗봇 메시지 API (`POST /api/v1/chat/`) — `content` + `ready` JSON, 정보 하나씩 물어보기
- [x] 추천 배치 API (`POST /api/v1/recommend/` 신설) — history 기반 배치 생성, LLM id 검증
- [x] 추천 히스토리 API (`GET /api/v1/recommendations/`) — 배치 중첩, ProductSerializer + reason
- [x] GMS 연동 (json_mode 미지원 대비, 프롬프트 강제 JSON)
- [x] 짧은 답변 + 한 번에 한 가지만 물어보기 (프롬프트 개선)
- [x] 사용량 제한 (하루 100번, Throttling 100/day)
- [x] 챗봇 응답 실패 에러 핸들링 (Timeout→504, ConnectionError→502)
- [x] 테스트 18개 (chat·recommend·history, mock 기반)

### UI 완성
- [x] 챗봇 UI (말풍선, 로딩 인디케이터)
- [x] 추천 카드 UI (이미지/이름/가격 인라인 표시)
- [x] 한 번에 3~5개 제품 추천 + 추천 이유 함께 표시
- [x] 추천 카드 클릭 → 올리브영 새 탭 이동
- [x] 찜하기 (추천 카드 바로 찜 등록/해제)
- [x] 추천 히스토리 UI
- [x] 제품 상세 UI

### Should 기능
- ❌ ~~피드백 (좋아요/별로예요)~~ — 포기
- ❌ ~~대시보드 차트~~ — 포기

### 보안 강화
- [x] SECRET_KEY 환경변수 분리 (.env 로드, 새 키 발급)
- [x] JWT 토큰 안전한 전달 (URL 쿼리스트링 제거 → 세션 임시 저장 → 교환 엔드포인트)
- [x] 이메일 중복 가입 차단 (provider_id 기준 식별, 이메일 선점 시 명시적 오류)
- [x] JWT 블랙리스트 활성화 (로그아웃 시 자동 폐기)
- [x] DRF Throttling (비인증 20/h, 인증 100/h)
- [x] 입력 검증 강화 (SkinProfile JSONField 타입 + 길이 검증)
- [x] 자동 토큰 갱신 (401 발생 시 /auth/token/refresh → 재시도)
- [x] 테스트 커버리지 (accounts 인증 플로우 7가지 단위 테스트)
- [x] 배포 전 보안·안정성 보강 (docs/backend-hardening.md)
  - DEBUG/ALLOWED_HOSTS 환경변수 분리 (fail-safe 기본값 False)
  - refresh 쿠키 Secure 적용 (`secure=not DEBUG`, 운영 HTTPS 전용)
  - LLM 엔드포인트 전용 throttle (ScopedRateThrottle — 대화 `chat` 100/day, 추천 `recommend` 20/day로 분리)
  - GMS 응답 파싱 502 방어, 추천 3개 상한, UserInfo 예외 가드, print→logging
- ❌ ~~서버사이드 사용량 정밀 카운팅 (UsageLog 모델)~~ — 포기
  - LLM 전용 ScopedRateThrottle(chat 100/day·recommend 20/day)로 일일 한도 목적 달성. UsageLog는 분석용이라 후순위

### AI 고도화 — RAG · LangChain · 관측 (Phase 2 핵심)
> 목표: 추천 레이어를 **"전 제품 프롬프트 주입" → "의미 기반 벡터 검색(RAG)"** 으로 전환.
> 설계·개념·운영 가이드는 [docs/rag.md](./rag.md) 참고.
- [x] GMS 임베딩 엔드포인트 검증 (`text-embedding-3-small`, dim 1536, 200 OK)
- [x] pgvector 도입 (docker 이미지 `pgvector/pgvector:pg16`, `CREATE EXTENSION vector`)
- [x] `Product.embedding` 필드(1536d) + 마이그레이션(VectorExtension)
- [x] 임베딩 서비스 모듈 (`chat/embeddings.py` — GMS embeddings 호출)
- [x] 임베딩 백필 관리 명령 (`backfill_embeddings`, ai_summary 보유 69건 적재)
- [x] **추천 검색 교체** (대화 임베딩 → 코사인 top-N → 그 N개만 프롬프트, 실패 시 리뷰순 폴백)
- [x] RAG 검색 테스트 (벡터 경로/폴백 경로/임베딩 정렬 — 전체 38개 통과)
- [x] **하이브리드 추천 (정형 제약 SQL 필터 + RAG)** — 설계: docs/README.md §3-A, docs/recommend-hybrid-contract.md
  - [x] `Product.form`(ArrayField, 복수 제형) + 규칙 백필 `backfill_form` (96건, 멀티값 4건)
  - [x] 제약 추출(규칙: 가격·제형) → SQL 필터(`form__overlap`/price/category) → 단계적 완화(MIN_POOL=3, 가격±1만→제형→카테고리)
  - [x] `constraints` 메타(완화 추적·note) + 제품별 `form`·`meets`(충족여부) 직렬화
  - [x] 추천 프롬프트에 가격·제형 노출 (A7)
  - [x] PostgreSQL 전용화 (SQLite 폴백 제거 — ArrayField/pgvector 의존)
  - [ ] A8 계약서 보완(추출 1급 승격·우선순위·하드/소프트 분리) / 라이브 회귀 테스트 보강
- [ ] ~~LangChain 파이프라인화~~ — 도입 보류(직접 호출이 더 단순, README §3-B)
- [x] **LLM 관측 배선 (LangSmith `@traceable`)** — `_call_gms`·`_resolve_constraints`·`_recommend_candidates`에 부착, 미설정 시 no-op (chat/observability.py). 활성화는 키 설정만 하면 됨.
- [x] **챗봇 대화 품질 개선 (README §3-F, Phase 1~3)**
  - [x] 프롬프트 그라운딩 — 추천 필터 축(제품군·제형 enum·가격·고민)으로 질문 한정, 못 쓰는 축(향료·성분·SPF·세부 텍스처) 차단
  - [x] 행동 규칙 — "모름/적당히" 수용·슬롯 스킵, 재질문 금지, 쉬운 말, 라벨 확인 떠넘김 금지, 제품군 특정 시 빠른 ready
  - [x] 라이브 데이터 그라운딩 — 대화 중 실제 재고를 SQL로 읽어 주입(_availability_hint, A3+A4 재활용)
  - [x] 가격 추출 천원·"N만M천원" 지원 보강

### 커뮤니티 — 용도별 게시판 (F1303 필수 요건) ✅ 백엔드 완료
> 명세서 F1303(유저 소통)·F1304(RESTful)·NF1304(5페이지+) 충족용.
> 앱 이름은 `board` (`community`가 파이썬 모듈명과 충돌해 변경). 컨셉: 용도별 게시판(자유 `free` / Q&A·팁 `qna` / 세일 정보 `sale`) + 제품 태그(게시글↔제품 양방향 연결).
> - 정참조: 게시글 → 태그된 제품 (`Post.product`)
> - 역참조: 제품 상세 → 그 제품 태그된 글 목록 (`Product.tagged_posts`, `GET /products/{id}/posts/`)
- [x] `board` 앱 생성 + 모델 3종 (`Post`(UUID PK)/`Comment`/`PostLike`)
- [x] 마이그레이션 (board 0001)
- [x] 게시판 CRUD API (목록 `?category=` 필터·상세·작성·수정/삭제 작성자 검증)
- [x] 댓글 API (작성·삭제, 작성자 검증)
- [x] 좋아요 토글 API (`PostLike` — 기존 찜 `Like` 패턴 재사용, 멱등)
- [x] **제품 역참조 API** (`GET /api/v1/products/{id}/posts/` — 제품 태그된 글, RESTful 관계 표현)
- [x] `board_seed.json` fixture (데모 유저·글 7·댓글 5·좋아요 3, 제품 태그 2건)
- [x] 테스트 (글 CRUD·댓글·좋아요·IDOR·역참조 — board 20개, 전체 58개 통과)
- [ ] 프론트: 게시판 5개 페이지 (목록/상세/작성/수정/내 글) + 제품 상세 "관련 글 N개" 섹션 + 네비 진입점

### 배포·QA
> DB 전환 상세 문서는 Notion 참고 (SQLite→PostgreSQL 전환·Docker 도입·트러블슈팅)
- [x] PostgreSQL 전환 (SQLite → 동시성·데이터 안정성 개선)
  - docker-compose로 PostgreSQL 16 구동 (UTF-8 인코딩 고정, healthcheck, 데이터 볼륨)
  - settings DATABASES 환경변수화 (DB_ENGINE 미설정 시 SQLite 폴백 → 점진적 전환)
  - psycopg2-binary 추가, Product 156건 dumpdata→loaddata 이관, 테스트 34개 통과
  - URLField max_length 200→500 (PG 길이 강제 대응, 올리브영 URL 최대 298자)
- [~] Docker 컨테이너화 (DB만 컨테이너로 구동 / 앱 컨테이너화는 배포 단계)
- [ ] **AWS EC2 배포 + GitHub Actions CI/CD** → 계획: [docs/deployment.md](./deployment.md)
  - [x] Phase 1: 배포 가능화 (localhost env화·gunicorn·Dockerfile·nginx.conf·compose.prod·.env.prod.example)
    - 회귀 테스트 63개 통과 (Phase1 변경 후 재확인)
    - 로컬에서 `docker-compose.prod.yml` 기동 검증 (nginx·backend·db, SPA·API·admin·static 응답 확인)
    - 검증 중 버그 발견·수정: `db` 서비스 변수치환용 루트 `.env` 누락 → 빈 자격증명 초기화 위험 (상세: deployment.md "로컬 검증 트러블슈팅")
    - 루트 `.env.prod.example` 추가, `.gitignore`에 `!.env.prod.example` 예외 추가
  - [x] 프론트 API base env화 (FE 담당, PR #49 `fix/api-base-env`) — `config.js`의 `API_BASE`가
    `VITE_API_BASE`(`.env.production`)를 읽도록 전환, 하드코딩 호출 잔존 없음 확인
  - [~] Phase 2: EC2 수동 배포 (진행 중)
    - EC2 생성(t3.micro, Ubuntu 24.04, 보안그룹 22/80/443), Docker+compose 설치, 스왑 2GB
    - 도메인 A레코드(GoDaddy) → 퍼블릭 IP 연결
    - 배포 브랜치에 `develop`(FE 작업분) merge — 파일 겹침 없어 무충돌
    - 코드 배포 + env 2개 주입 + `docker compose -f docker-compose.prod.yml up -d --build` 기동
    - migrate 정상 적용, **`products_seed.json` 스테일 발견·갱신**(156건→306건, 임베딩·제형 포함) —
      상세: deployment.md "프로덕션 데이터 적재 트러블슈팅"
    - 남음: certbot HTTPS, OAuth redirect 등록, 프론트 dist 배포, E2E 검증
  - [ ] Phase 3: Actions (CI 테스트 + CD 자동 배포)
- [x] DEBUG/ALLOWED_HOSTS 환경변수 분리 (배포 시 `.env`만 주입하면 운영 전환 — backend-hardening.md)
- [ ] 전체 QA·버그 수정
- [ ] 발표 준비
