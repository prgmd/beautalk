# 프로젝트 구조

## 인프라 (프로젝트 루트)

```
docker-compose.yml    # 로컬 개발 인프라 (PostgreSQL 16 컨테이너)
│   └── db 서비스: postgres:16, UTF-8 인코딩 고정, healthcheck, 데이터 볼륨(postgres_data)
│       사용법: docker compose up -d  →  migrate  →  loaddata
```

> DB를 SQLite → PostgreSQL로 전환하며 컨테이너로 구동. 접속정보는 `backend/.env`의 `DB_*` 값과 일치.
> 앱(Django) 자체의 컨테이너화는 배포 단계에서 `docker-compose.yml`에 backend 서비스를 추가해 진행 예정.

## Backend (`backend/`)

```
config/
├── settings.py       # Django 설정 (SIMPLE_JWT, CORS, Throttling, 환경변수 로드)
│   └── DATABASES: 환경변수 기반 (DB_ENGINE 미설정 시 SQLite 폴백, 설정 시 PostgreSQL)
├── urls.py           # 루트 URL 라우팅 (accounts 앱 포함)

accounts/
├── models.py         # UserInfo, SkinProfile 모델
├── serializers.py    # SkinProfileSerializer (JSONField 검증), UserInfoSerializer
├── views.py          # ProfileView, OAuth views (Login/Callback), Token 관리 (Exchange/Refresh/Logout)
│   ├── ProfileView                # GET/POST/PATCH /api/v1/profile
│   ├── KakaoLoginView            # GET /api/v1/auth/kakao/login (state 생성)
│   ├── KakaoCallbackView         # GET /api/v1/auth/kakao/callback (state 검증, 에러처리)
│   ├── GoogleLoginView           # GET /api/v1/auth/google/login (state 생성)
│   ├── GoogleCallbackView        # GET /api/v1/auth/google/callback (state 검증, 에러처리)
│   ├── TokenExchangeView         # GET /api/v1/auth/exchange (세션 토큰 → HttpOnly 쿠키)
│   ├── CookieTokenRefreshView    # POST /api/v1/auth/token/refresh (쿠키 갱신)
│   ├── LogoutView                # POST /api/v1/auth/logout (블랙리스트 + 쿠키 삭제)
│   ├── AccountView               # GET/DELETE /api/v1/account (계정 조회 + 회원 탈퇴)
│   └── resolve_oauth_user()      # Helper: provider_id 기준 사용자 식별
├── urls.py           # accounts 앱 URL 라우팅
├── tests.py          # OAuth/Token/SkinProfile/회원탈퇴 검증 테스트 8가지

products/
├── models.py         # Product, Review, Like, InUseProduct 모델
├── serializers.py    # ProductSerializer, LikeSerializer (제품 중첩)
├── views.py          # 제품 조회 + 찜 API
│   ├── ProductListView          # GET /api/v1/products/ (페이지네이션, ?category 필터)
│   ├── ProductDetailView        # GET /api/v1/products/<uuid>/
│   ├── LikeListCreateView       # GET/POST /api/v1/likes/ (내 찜 목록 / 추가)
│   └── LikeDeleteView           # DELETE /api/v1/likes/<uuid>/ (product_id 기준, IDOR 방어)
├── urls.py           # products 앱 URL 라우팅
├── tests.py          # 찜·제품 API 테스트 8가지

chat/
├── models.py         # Recommendation 모델
├── serializers.py    # RecommendationSerializer
├── views.py          # 챗봇 + 추천 기록 API
│   ├── ChatView                     # POST /api/v1/chat/ (GMS LLM 호출, Stateless)
│   │   └── _build_system_prompt()   # 피부 프로필 + 전체 제품 ai_summary → 시스템 프롬프트 조립
│   └── RecommendationListCreateView # GET/POST /api/v1/recommendations/
├── urls.py           # chat 앱 URL 라우팅
├── tests.py          # 챗봇(mock) + 추천 기록 테스트 10가지

crawling.py           # 크롤링 스크립트
products_seed.json    # Product 156건 시드 (SQLite→PG 이관용 fixture, loaddata로 적재)
requirements.txt      # 의존성 (psycopg2-binary 포함 — PostgreSQL 드라이버)

.env                  # 환경변수 (git 제외)
│   DJANGO_SECRET_KEY=...
│   KAKAO_CLIENT_ID=...
│   KAKAO_CLIENT_SECRET=...   # 카카오 앱 > 보안 > 클라이언트 시크릿 코드 (활성화 ON 필수)
│   GOOGLE_CLIENT_ID=...
│   GOOGLE_CLIENT_SECRET=...
│   GMS_API_KEY=...
│   GMS_API_URL=https://gms.ssafy.io/gmsapi/api.openai.com/v1/chat/completions
│   GMS_MODEL=gpt-5-nano
│   DB_ENGINE=django.db.backends.postgresql   # 미설정 시 SQLite 폴백
│   DB_NAME / DB_USER / DB_PASSWORD / DB_HOST / DB_PORT
```

> 챗봇은 GMS(`gpt-5-nano`)를 `POST https://gms.ssafy.io/gmsapi/api.openai.com/v1/chat/completions`로
> 직접 호출하는 Stateless 구조. 프론트가 `history[]`를 관리해 매 요청마다 전송한다.
> 서버사이드 사용량 제한 / RAG(pgvector)는 Phase 2. 근거: `docs/backend-api-report.md`

## Frontend (`frontend/src/`)

```
router/
└── index.js          # 라우트 정의 + beforeEach 가드

stores/
├── auth.js           # 로그인 상태 + access 토큰 메모리 관리 (Pinia)
│   ├── user: { hasProfile }      # localStorage 유지 (refresh 시에도 복원)
│   ├── accessToken: string       # 메모리에만 유지 (XSS 방지)
│   └── setAccessToken()          # startup refresh로 호출됨
├── chat.js           # 채팅 상태
├── profile.js        # 프로필 상태
└── productDetail.js  # 상품 상세 상태

views/
├── LoginView.vue         # 로그인 페이지 (OAuth 로그인 버튼)
├── AuthCallbackView.vue  # OAuth 콜백 처리
│   └── /auth/exchange 엔드포인트로 세션 토큰 교환
│       → access 응답 바디 저장, refresh는 HttpOnly 쿠키로 자동 관리
├── OnboardingView.vue    # 온보딩 (피부 프로필 입력, JSONField 검증)
├── ChatView.vue          # 챗봇 메인
└── mypage/
    ├── MyPageLayout.vue
    ├── SkinProfileView.vue
    ├── LikedProductsView.vue
    ├── RecommendedProductsView.vue
    └── AccountView.vue   # 로그아웃 (토큰 블랙리스트)

services/
├── api.js            # API 요청 래퍼 (credentials, 401 자동 갱신 인터셉터)
│   ├── request()     # fetch 호출 + Authorization 헤더 + 쿠키 전송
│   ├── tryRefresh()  # 401 시 /auth/token/refresh 호출 → access 갱신
│   └── get/post/patch/del  # 편의 메서드

components/
├── GlobalSidebar.vue         # 네비게이션 바 (로그아웃 포함)
└── ProductDetailModal.vue    # 제품 상세 모달
```
