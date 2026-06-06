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
- [ ] 구글 OAuth 연동
- [x] JWT 토큰 발급 및 갱신
- [x] Vue 라우터 가드
- [ ] 온보딩 스킵 시 챗봇 진입 처리

### 온보딩 UI·API
- [ ] 피부 타입 선택 UI (건성/지성/복합성/민감성)
- [ ] 피부 고민 선택 UI (여드름/주름/색소침착/모공 등 다중 선택)
- [ ] 기피 성분 입력 UI (알레르기/기피 성분 다중 선택)
- [ ] 온보딩 데이터 백엔드 저장
- [ ] 프로필 지정 → 챗봇 추천 자동 참조 연동

### 프로필 API·UI
- [x] Serializer 작성 (SkinProfileSerializer, UserInfoSerializer)
- [x] 프로필 조회/생성/수정 API (GET, POST, PATCH /api/v1/profile)
- [x] URL 연결 (accounts/urls.py, config/urls.py)
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
