# 프로젝트 구조

## Backend (`backend/`)

```
config/
├── settings.py       # Django 설정 (JWT, CORS, 환경변수 로드)
├── urls.py           # 루트 URL 라우팅 (token, profile, kakao callback)

accounts/
├── models.py         # UserInfo, SkinProfile 모델
├── serializers.py    # SkinProfileSerializer
├── views.py          # ProfileView, KakaoCallbackView
├── urls.py           # accounts 앱 URL 라우팅

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
├── auth.js           # 토큰/로그인 상태 관리 (Pinia)
├── chat.js           # 채팅 상태
├── profile.js        # 프로필 상태
└── productDetail.js  # 상품 상세 상태

views/
├── LoginView.vue         # 로그인 페이지
├── AuthCallbackView.vue  # OAuth 콜백 처리 (토큰 저장 → 라우팅)
├── OnboardingView.vue    # 온보딩 (피부 프로필 입력)
├── ChatView.vue          # 챗봇 메인
└── mypage/
    ├── MyPageLayout.vue
    ├── SkinProfileView.vue
    ├── LikedProductsView.vue
    ├── RecommendedProductsView.vue
    └── AccountView.vue

components/
├── GlobalSidebar.vue
└── ProductDetailModal.vue
```
