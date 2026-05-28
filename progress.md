# Beautalk — 진행 현황

---

## ✅ 완료

### 프로젝트 세팅
- [x] 주제 선정 / 기능 명세 회의
- [x] 레포지토리 생성 (private)
- [x] Collaborator 초대
- [x] 브랜치 룰셋 설정 (`protect-main`, `dev_rule`)
- [x] PR 템플릿 추가 (`.github/PULL_REQUEST_TEMPLATE.md`)
- [x] `.gitignore` 추가
- [x] `README.md` 초안 작성
- [x] default 브랜치 → `develop`으로 변경

### Django·Vue 초기화
- [x] Django 프로젝트 생성 (`config`)
- [x] 패키지 설치 (`DRF`, `django-cors-headers`, `python-dotenv`, `simplejwt`)
- [x] `settings.py` 수정 (INSTALLED_APPS, MIDDLEWARE, CORS, REST_FRAMEWORK, 언어/타임존)
- [x] Vue 3 프로젝트 생성 (`beautalk-frontend`)
- [x] Vue 옵션 설정 (Router, Pinia, ESLint, Prettier)
- [x] DB 초기 마이그레이션 (`python manage.py migrate`)
- [x] `requirements.txt` 저장
- [x] 앱 구조 설계 (`accounts`, `products`, `chat`)
- [x] 모델 작성 (UserInfo, SkinProfile, Product, Like, InUseProduct, Recommendation)
- [x] 모델 마이그레이션

### 기획 및 설계
- [x] 기능명세서 v1.0 작성
- [x] 와이어프레임 완성
- [x] 유스케이스 목록 도출 (UC-01 ~ UC-14)
- [x] 유스케이스 다이어그램 작성
- [x] ERD 설계 (요구사항 분석 → 엔티티 도출 → 속성/식별자 정의 → 관계 설정 → 차수 분석)
- [x] ERDCloud / dbdiagram.io로 ERD 다이어그램 작성
- [x] API 명세서 작성 (Request Body, Response, Status Code 포함)

### 크롤링 스크립트
- [x] 올리브영 `robots.txt` 확인 → 베스트 리스트 + 상품 상세 허용 확인
- [x] 크롤링 도구 확정 → undetected_chromedriver (Cloudflare bypass)
- [x] 크롤링 카테고리 범위 결정 → 4개 (스킨케어, 클렌징, 선케어, 메이크업)
- [x] 크롤링 스크립트 작성
- [x] 상품 기본정보 수집 (brand, name, price, image_url, category, oliveyoung_url) + DB 저장
- [x] Product 모델 확장 (ai_summary, satisfaction_by_type)
- [x] Review 모델 신규 생성 (text, rating, user_name, recommend_count, review_date)
- [x] 마이그레이션 적용
- [x] 리뷰 데이터 수집 (API 기반, 제품당 10개)
- [x] 타입별 만족도 수집 (Stats API로 가장 높은 선택 옵션 추출)
- [x] Gemini API로 리뷰 요약 → `Product.ai_summary` 저장

---

## 🔲 진행 예정

### OAuth
- [ ] 카카오 OAuth 연동
- [ ] 구글 OAuth 연동
- [ ] JWT 토큰 발급 및 갱신
- [ ] Vue 라우터 가드
- [ ] 온보딩 스킵 시 챗봇 진입 처리

### 온보딩 UI·API
- [ ] 피부 타입 선택 UI (건성/지성/복합성/민감성)
- [ ] 피부 고민 선택 UI (여드름/주름/색소침착/모공 등 다중 선택)
- [ ] 기피 성분 입력 UI (알레르기/기피 성분 다중 선택)
- [ ] 온보딩 데이터 백엔드 저장
- [ ] 프로필 지정 → 챗봇 추천 자동 참조 연동

### 프로필 API·UI
- [ ] 프로필 조회/수정 API
- [ ] 마이페이지 UI (피부 프로필 확인 및 수정)
- [ ] 찜한 제품 리스트 확인 및 올리브영 링크 이동
- [ ] 로그아웃 / 회원 탈퇴

### 챗봇 API
> 아키텍처: GMS(SSAFY 제공 LLM) 직접 호출 방식. 프로필 + 제품 목록(ai_summary 포함) → LLM 컨텍스트 주입. 프론트엔드가 대화 기록(`history[]`) 관리, 백엔드는 stateless.
- [ ] 챗봇 메시지 API (`POST /api/v1/chat`) — `content` + `history[]` 수신
- [ ] GMS 연동 (프로필 + 전체 제품 ai_summary → LLM 컨텍스트 구성)
- [ ] 자연어 질문 이해 → 피부 프로필 자동 참조 답변 생성
- [ ] 기피 성분 필터링 로직
- [ ] 화장품 외 질문 범위 제한
- [ ] 후속 질문 처리 (history[] 기반 대화 맥락 유지)
- [ ] 챗봇 응답 실패 에러 핸들링

### UI 완성
- [ ] 챗봇 UI (말풍선, 로딩 인디케이터)
- [ ] 추천 카드 UI (이미지/이름/가격 인라인 표시)
- [ ] 한 번에 3~5개 제품 추천 + 추천 이유 함께 표시
- [ ] 추천 카드 클릭 → 올리브영 새 탭 이동
- [ ] 찜하기 (추천 카드 바로 찜 등록/해제)
- [ ] 추천 히스토리 UI
- [ ] 제품 상세 UI

### Should 기능
- [ ] 피드백 (좋아요/별로예요)
- [ ] 대시보드 차트

### 배포·QA
- [ ] Docker 컨테이너화
- [ ] AWS 배포·Nginx 설정
- [ ] 전체 QA·버그 수정
- [ ] 발표 준비
