# 프로젝트 구조

## Backend (`backend/`)

```
config/
├── settings.py       # Django 설정 (SIMPLE_JWT, CORS, Throttling, 환경변수 로드)
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
│   └── resolve_oauth_user()      # Helper: provider_id 기준 사용자 식별
├── urls.py           # accounts 앱 URL 라우팅
├── tests.py          # OAuth/Token/SkinProfile 검증 테스트 7가지

products/
├── models.py         # Product, Review 모델

chat/
├── models.py         # Chat 관련 모델

crawling.py           # 크롤링 스크립트
```

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
