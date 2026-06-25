# 명세서 요구사항 충족 정리 (어필)

> "AI 기반 추천 서비스 (13회차)" 명세서의 **필수 요구사항을 모두 충족**했고, **심화 과제(배포)까지** 완료했습니다.
> beautalk는 명세서의 예시 도메인(도서)을 **화장품**으로 바꿔, 같은 요구사항을 더 깊게 구현한 프로젝트입니다.

이 문서는 발표·제출 시 "명세서에서 시킨 걸 우리가 어떻게 했는가"에 한 장으로 답하기 위한 자료입니다.

---

## 1. 한눈에 보는 충족 현황

### 기능적 요구사항

| 번호 | 요구사항 | 우선순위 | 충족 | 우리 구현 (핵심 근거) |
|------|----------|:---:|:---:|------|
| **F1301** | 사용자 추천 | 필수 | ✅ | **대화형 하이브리드 추천** — 문답으로 조건을 모아, SQL 필터(가격·제형)로 거른 뒤 AI 의미검색(RAG)으로 정렬해 제품 추천 |
| **F1302** | API 활용 | 필수 | ✅ | **GMS(LLM) API** — 대화·추천·리뷰 요약·임베딩 / **카카오·구글 OAuth API** — 소셜 로그인 |
| **F1303** | 커뮤니티 | 필수 | ✅ | **용도별 게시판**(자유·Q&A·세일) + 댓글 + 좋아요 + **제품 태그**(글↔제품 연결) |
| **F1304** | RESTful 원칙 | 필수 | ✅ | 자원 중심 URL + HTTP 메서드별 의미(GET/POST/PATCH/DELETE) + 상황별 상태코드(200·201·204·400·401·403·404·502·504) |
| **F1305** | 서비스 배포 | **심화** | ✅ | **AWS EC2 + Docker + Nginx + HTTPS** 실배포 → `https://beautalk.site` |

### 비기능적 요구사항

| 번호 | 요구사항 | 충족 | 우리 구현 (핵심 근거) |
|------|----------|:---:|------|
| **NF1301** | Git 활용 | ✅ | `develop` + 기능 브랜치 + **Pull Request 리뷰** 전략, 한글 커밋 컨벤션, 브랜치 룰셋·PR 템플릿 |
| **NF1302** | API Key 관리 | ✅ | **시크릿 0건 커밋** — SECRET_KEY·DB비번·OAuth·LLM 키 전부 `.env` 분리(dotenv/Vite), `.gitignore` 차단 |
| **NF1303** | 데이터 확보 | ✅ | 올리브영 제품 **306종**(중복 제거 후) 크롤링 + AI 요약(커버리지 99.7%) + 정제, **`loaddata` 가능한 fixture**(`products_seed.json`, `board_seed.json`) |
| **NF1304** | 페이지 다양성 | ✅ | 화면 **약 13개**(커뮤니티만 4개) — 요구 기준 "5개+"를 여유 있게 초과 |

---

## 2. 요구사항별 상세 어필

### F1301 사용자 추천 — "기술적으로 설명 가능한 추천"
명세서는 *"어떠한 방식으로 추천 시스템을 구현했는지 기술적으로 설명 가능해야 함"* 을 요구합니다. 우리 추천은 한 문장으로 설명됩니다:

> **하드 조건(가격·제형)은 SQL이 보장하고, 부드러운 취향(끈적임·진정감 등)은 AI 의미검색(RAG)이 맡는 2겹 구조.**

- ① **문답으로 조건 수집**(대화 단계) → ② **SQL 정형 필터**로 조건 안 맞는 제품을 후보에서 아예 제외 → ③ 남은 후보를 **pgvector 임베딩 코사인 유사도**로 정렬(RAG) → ④ 그 후보만 LLM이 보고 골라 **추천 이유**까지 작성.
- 효과: AI가 조건 위반 제품을 **볼 수조차 없어** "로션 요청에 크림" 같은 오추천이 **구조적으로 불가능**.
- 후보가 부족하면 **단계적으로 조건을 풀고(완화), 무엇을 풀었는지 사용자에게 정직하게 표기**(✓/✗ 배지).
- 상세: [개발 이력 07](development-history/07-rag-hybrid-recommendation.md), [recommend-failure-report.md](recommend-failure-report.md), [recommend-hybrid-contract.md](recommend-hybrid-contract.md)

### F1302 API 활용 — "직접 구현하기 힘든 기능을 API로"
- **생성형 AI(GMS, SSAFY OpenAI 프록시)**: 자연어 대화, 추천 이유 생성, 리뷰 요약(`ai_summary`), 텍스트 임베딩(`text-embedding-3-small`, 1536차원). 직접 만들 수 없는 자연어 이해를 API로 해결.
- **카카오·구글 OAuth 2.0**: 자체 비밀번호를 저장하지 않고 신원 확인을 위임 → 더 안전.
- 상세: [개발 이력 06](development-history/06-chatbot-recommendation.md), [05](development-history/05-auth-security.md)

### F1303 커뮤니티 — "다양한 방식의 소통"
- **용도별 게시판**(자유 / Q&A·팁 / 세일 정보)으로 소통 맥락을 분리.
- 글 + **댓글** + **좋아요**(토글)로 다층 소통.
- **제품 태그(M2M)**: 글에 제품을 달면, 제품 상세에서 "이 제품 관련 글 N개"로 **역참조** — 추천과 커뮤니티가 연결됨.
- 상세: [개발 이력 08](development-history/08-community.md)

### F1304 RESTful 원칙 — "메서드와 상태코드를 제대로"
- URL은 자원(`/posts/`, `/posts/{id}/comments/`), 메서드는 행위(GET 조회·POST 생성·PATCH 수정·DELETE 삭제).
- 상태코드로 결과를 명확히: 생성 201, 삭제 204, 권한 없음 403, 못 찾음 404, 외부 LLM 실패 502/504 등.
- 전체 **23개 엔드포인트**가 `api/v1/` 아래 일관된 규칙. 상세: [개발 이력 02](development-history/02-design.md)

### F1305 서비스 배포 (심화) — 실제로 인터넷에 띄움
- AWS EC2 한 대에 **Docker Compose 3개 컨테이너**(PostgreSQL+pgvector / Django(gunicorn) / Nginx).
- Nginx가 Vue 정적 빌드 서빙 + `/api` 프록시. **Let's Encrypt 무료 인증서로 HTTPS** 적용.
- 결과: **https://beautalk.site** 누구나 접속 가능. 상세: [개발 이력 10](development-history/10-deployment.md)

### NF1301 Git 활용 — "충돌 없이 함께"
- 전략: `develop`(통합) + `feature/*`(기능별) + **PR 리뷰 후 머지**. main 직접 푸시 금지(브랜치 보호).
- 커밋 메시지는 목적이 드러나는 한글 컨벤션(feat/fix/chore/docs).
- 상세: [개발 이력 03](development-history/03-collaboration.md)

### NF1302 API Key 관리 — "키는 코드에 없다" ⭐
- SECRET_KEY·DB 비밀번호·카카오/구글 client secret·**유료 GMS(LLM) API 키**를 전부 `os.environ.get`(dotenv)으로 분리. 프론트는 Vite 환경변수로 공개 URL만 노출.
- `.gitignore`가 모든 `.env`를 차단하며, **git 히스토리 전체에 키 커밋 0건**.
- 시연 가능한 증거: `git ls-files | grep env` → 시크릿 아닌 공개 URL 파일 하나만 반환.
- 상세: [개발 이력 05](development-history/05-auth-security.md)

### NF1303 데이터 확보 — "충분하고 재현 가능한 데이터"
- 올리브영 제품 **306종**(스킨케어·클렌징·선케어·메이크업, 중복 제거 후) 크롤링, 리뷰를 AI로 요약(커버리지 99.7%), 중복·가격·URL 정제.
- **`loaddata`로 한 번에 적재되는 fixture** 제공(명세서가 요구한 형식). 상세: [개발 이력 04](development-history/04-data.md)

### NF1304 페이지 다양성 — "5개+"
- 로그인 / 온보딩 / 챗봇 / 카탈로그 / 커뮤니티(목록·작성·상세·수정) / 마이페이지(프로필·찜·추천내역·계정) 등 **약 13개 화면**. 요구 기준을 크게 초과.
- 상세: [개발 이력 09](development-history/09-frontend-design.md)

---

## 3. 제출용 README 필수 항목 체크 (명세서 1.6)

명세서가 README에 포함하라고 한 항목 A~H의 충족 위치입니다. (루트 [README.md](../README.md)에 통합)

| 항목 | 요구 | 충족 위치 |
|------|------|----------|
| A | 팀원 정보 및 업무 분담 | README §팀 |
| B | 목표 서비스 및 실제 구현 정도 | README §서비스 소개 + 본 문서 §1 |
| C | 데이터베이스 모델링 (ERD) | [개발 이력 02](development-history/02-design.md) |
| D | 추천 알고리즘 기술적 설명 | [개발 이력 07](development-history/07-rag-hybrid-recommendation.md) |
| E | 핵심 기능 설명 | README §핵심 기능 + 개발 이력 06~09 |
| F | 생성형 AI 활용 부분 | [개발 이력 04](development-history/04-data.md)·[06](development-history/06-chatbot-recommendation.md)·[07](development-history/07-rag-hybrid-recommendation.md) |
| G | 서비스 URL (배포) | https://beautalk.site |
| H | 기타 (기획·설계 문서 전체) | [docs 폴더](README.md) |

---

## 4. 한 줄 결론

> **필수 요구사항 9개 전부 + 심화(배포)까지 충족.** 특히 추천(F1301)은 "AI가 의미만 비슷한 걸 고르는" 흔한 한계를 **SQL+RAG 하이브리드**로 정면 돌파했고, 보안(NF1302)은 **키 0건 커밋**으로 증명 가능합니다.
