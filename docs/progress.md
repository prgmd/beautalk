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
> - 토큰 효율: Phase 2에서 RAG 벡터 검색으로 개선 예정
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
- [ ] 피드백 (좋아요/별로예요)
- [ ] 대시보드 차트

### 보안 강화
- [x] SECRET_KEY 환경변수 분리 (.env 로드, 새 키 발급)
- [x] JWT 토큰 안전한 전달 (URL 쿼리스트링 제거 → 세션 임시 저장 → 교환 엔드포인트)
- [x] 이메일 중복 가입 차단 (provider_id 기준 식별, 이메일 선점 시 명시적 오류)
- [x] JWT 블랙리스트 활성화 (로그아웃 시 자동 폐기)
- [x] DRF Throttling (비인증 20/h, 인증 100/h)
- [x] 입력 검증 강화 (SkinProfile JSONField 타입 + 길이 검증)
- [x] 자동 토큰 갱신 (401 발생 시 /auth/token/refresh → 재시도)
- [x] 테스트 커버리지 (accounts 인증 플로우 7가지 단위 테스트)

### 배포·QA
- [ ] Docker 컨테이너화
- [ ] AWS 배포·Nginx 설정
- [ ] PostgreSQL 전환 (SQLite → 동시성, 데이터 안정성 개선)
- [ ] 전체 QA·버그 수정
- [ ] 발표 준비
