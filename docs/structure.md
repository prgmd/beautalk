# 프로젝트 구조

## 인프라 (프로젝트 루트)

```
docker-compose.yml    # 로컬 개발 인프라 (PostgreSQL 16 + pgvector 컨테이너)
│   └── db 서비스: pgvector/pgvector:pg16, UTF-8 인코딩 고정, healthcheck, 데이터 볼륨(postgres_data)
│       사용법: docker compose up -d  →  migrate  →  loaddata  →  backfill_embeddings
```

> DB를 SQLite → PostgreSQL로 전환하며 컨테이너로 구동. 접속정보는 `backend/.env`의 `DB_*` 값과 일치.
> 앱(Django) 자체의 컨테이너화는 배포 단계에서 `docker-compose.yml`에 backend 서비스를 추가해 진행 예정.

## Backend (`backend/`)

```
config/
├── settings.py       # Django 설정 (SIMPLE_JWT, CORS, Throttling, 환경변수 로드)
│   └── DATABASES: PostgreSQL 전용 (.env의 DB_* 주입; pgvector·ArrayField 의존으로 SQLite 폴백 제거)
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
│   ├── Product.embedding: VectorField(1536) — RAG 벡터 검색용 (pgvector)
│   └── Product.form: ArrayField(제형, 복수) — 하이브리드 SQL 필터 축 (FORM_CHOICES 10종)
├── serializers.py    # ProductSerializer(form 포함), LikeSerializer (제품 중첩)
├── views.py          # 제품 조회 + 찜 API
│   ├── ProductListView          # GET /api/v1/products/ (페이지네이션, ?category 필터)
│   ├── ProductDetailView        # GET /api/v1/products/<uuid>/
│   ├── LikeListCreateView       # GET/POST /api/v1/likes/ (내 찜 목록 / 추가)
│   ├── LikeDeleteView           # DELETE /api/v1/likes/<uuid>/ (product_id 기준, IDOR 방어)
│   └── ProductPostsView         # GET /api/v1/products/<uuid>/posts/ (역참조: 제품 태그된 글)
├── management/commands/
│   ├── backfill_embeddings.py   # 제품 → 임베딩 일괄 적재 (seed 미포함, 재생성)
│   └── backfill_form.py         # 제품명 규칙 파싱 → Product.form 백필 (멀티값, dry-run/--apply)
├── urls.py           # products 앱 URL 라우팅
├── tests.py          # 찜·제품 API 테스트 8가지

chat/
├── models.py         # Recommendation 모델
├── serializers.py    # RecommendationSerializer (제품별 form·meets 충족여부 포함)
├── embeddings.py     # GMS 임베딩 호출 (text-embedding-3-small) — 백필·검색 공용
├── views.py          # 챗봇 + 추천 + 추천 기록 API
│   ├── ChatView                     # POST /api/v1/chat/ (GMS LLM 호출, Stateless)
│   ├── RecommendView                # POST /api/v1/recommend/ (배치 생성, 선택적 filters)
│   │   ├── _recommend_candidates()  # 하이브리드: 제약추출 → SQL필터(form/price/category) → 단계적완화 → 임베딩 코사인 top-N
│   │   └── _build_recommend_prompt()# 후보(가격·제형 포함) → 시스템 프롬프트 조립
│   └── RecommendationListView       # GET /api/v1/recommendations/
├── urls.py           # chat 앱 URL 라우팅
├── tests.py          # 챗봇·추천(RAG 포함)·기록 테스트 (chat 22가지)

board/                # 커뮤니티 게시판 (F1303 필수 — 용도별: 자유/Q&A·팁/세일, 제품 태그)
│                     #   ※ 앱명 community는 파이썬 모듈명과 충돌해 board로 명명
├── models.py         # Post(카테고리·제목·본문 + 제품 정참조 FK, UUID PK), Comment, PostLike
│   └── Post.product: products.Product FK(SET_NULL) — 게시글↔제품 태그, related_name='tagged_posts'
├── serializers.py    # PostList/PostDetail/PostWrite(제품 product_id 입력) + CommentSerializer
├── views.py          # 게시판 + 댓글 + 좋아요 API (IsAuthorOrReadOnly로 작성자 검증)
│   ├── PostListCreateView       # GET/POST /api/v1/posts/ (?category= 필터, 페이지네이션)
│   ├── PostDetailView           # GET/PATCH/DELETE /api/v1/posts/<uuid>/ (수정·삭제 작성자만)
│   ├── CommentCreateView        # POST /api/v1/posts/<uuid>/comments/
│   ├── CommentDeleteView        # DELETE /api/v1/comments/<id>/ (작성자만, IDOR 방어)
│   └── PostLikeView             # POST/DELETE /api/v1/posts/<uuid>/like/ (좋아요 토글, 멱등)
├── urls.py           # board 앱 URL 라우팅
├── tests.py          # 게시판 CRUD·댓글·좋아요·IDOR·역참조 테스트 (board 20가지)

crawling.py           # 크롤링 스크립트
products_seed.json    # Product 156건 시드 (SQLite→PG 이관용 fixture, loaddata로 적재)
board_seed.json       # 게시판 데모 fixture (유저·글 7·댓글 5·좋아요 3, 제품 태그 2건, loaddata)
requirements.txt      # 의존성 (psycopg2-binary, pgvector — PostgreSQL + 벡터 검색)

.env                  # 환경변수 (git 제외)
│   DJANGO_SECRET_KEY=...
│   KAKAO_CLIENT_ID=...
│   KAKAO_CLIENT_SECRET=...   # 카카오 앱 > 보안 > 클라이언트 시크릿 코드 (활성화 ON 필수)
│   GOOGLE_CLIENT_ID=...
│   GOOGLE_CLIENT_SECRET=...
│   GMS_API_KEY=...
│   GMS_API_URL=https://gms.ssafy.io/gmsapi/api.openai.com/v1/chat/completions
│   GMS_MODEL=gpt-5-nano
│   GMS_EMBED_MODEL=text-embedding-3-small   # RAG 임베딩 모델 (미설정 시 기본값)
│   DB_ENGINE=django.db.backends.postgresql   # 미설정 시 SQLite 폴백
│   DB_NAME / DB_USER / DB_PASSWORD / DB_HOST / DB_PORT
```

> 챗봇은 GMS(`gpt-5-nano`)를 `POST https://gms.ssafy.io/gmsapi/api.openai.com/v1/chat/completions`로
> 직접 호출하는 Stateless 구조. 프론트가 `history[]`를 관리해 매 요청마다 전송한다.
> 서버사이드 사용량 제한 / RAG(pgvector)는 Phase 2.

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
