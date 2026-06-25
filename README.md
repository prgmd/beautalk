# Beautalk 🌿
> 당신의 뷰티 상담사, 뷰토크. — **대화하듯 물어보면 내 피부에 맞는 화장품을 추천해 주는 AI 서비스**

🔗 **서비스 URL: https://beautalk.site**

---

## 1. 서비스 소개

화장품은 성분·제형·내 피부 타입을 동시에 따져야 해서 입문자에게는 고르기가 막막합니다.
beautalk는 **AI 상담사 '뷰토크'와 대화**하면서 피부 타입·고민·예산을 자연스럽게 풀어놓으면, 그에 맞는 실제 제품(올리브영 데이터 기반)을 **이유와 함께** 추천합니다. 마음에 든 제품은 찜하고, 사용 후기는 커뮤니티에서 나눌 수 있습니다.

**핵심 한 줄:** *의미만 비슷한 추천이 아니라, 내 조건(예산·제형)을 반드시 지키는 추천.*

---

## 2. 팀원 및 업무 분담 *(명세 A)*

| 이름 | 역할 | 주요 담당 | GitHub |
|---|---|---|---|
| 김채은 | 프론트엔드 | Vue SPA·디자인 시스템·추천/커뮤니티 화면·배포(프론트) | https://github.com/c7aeun |
| 장준환 | 백엔드 | Django REST·인증/보안·데이터·하이브리드 추천(RAG)·배포(인프라) | https://github.com/prgmd |

> 협업은 `develop` + 기능 브랜치 + **PR 리뷰**로 진행하고, **API 계약서로 인터페이스를 먼저 합의**한 뒤 프론트·백엔드가 병렬로 개발했습니다. (→ [개발 이력 03](docs/development-history/03-collaboration.md))

---

## 3. 기술 스택

| 구분 | 기술 |
|---|---|
| Frontend | Vue 3 (`<script setup>`) · Pinia · Vue Router · Vite |
| Backend | Django 5.2 · Django REST Framework · SimpleJWT |
| Database | PostgreSQL 16 + **pgvector** (벡터 검색) |
| AI | GMS(OpenAI 호환) — `gpt-5-nano` 대화·추천, `text-embedding-3-small` 임베딩 |
| Infra | AWS EC2 · Docker Compose · Nginx · HTTPS(Let's Encrypt) |
| 인증 | 카카오 · 구글 OAuth 2.0 |

---

## 4. 핵심 기능 *(명세 E)*

- **AI 추천 챗봇** — 대화로 조건을 모아(대화 단계) → 제품 추천(추천 단계)으로 분리. 추천 이유·조건 충족 배지(✓/✗) 표시.
- **하이브리드 추천 엔진** — SQL 정형 필터(가격·제형) + RAG 의미검색. (아래 §5)
- **소셜 로그인 & 온보딩** — 카카오/구글 OAuth, 피부 타입·고민·기피 성분 프로필.
- **제품 카탈로그 & 찜** — 제품 목록/상세, AI 요약·피부타입별 만족도, 찜하기.
- **커뮤니티 게시판** — 용도별(자유·Q&A·세일) 글·댓글·좋아요, **제품 태그**로 글↔제품 연결.
- **마이페이지** — 프로필·찜 목록·추천 내역·계정/탈퇴.

화면 약 13개, REST API 23개. (→ [개발 이력 06~09](docs/development-history/))

---

## 5. 추천 알고리즘 기술적 설명 *(명세 D)*

> **하드 조건(가격·제형)은 SQL이 보장, 부드러운 취향은 AI 의미검색(RAG)이 담당하는 2겹 구조.**

1. **조건 수집(대화)** — 챗봇이 문답으로 제품군·제형·가격·피부고민을 모음.
2. **SQL 정형 필터** — 가격대·제형(`form` ArrayField overlap)·카테고리로 *조건 안 맞는 제품을 후보에서 아예 제외.*
3. **RAG 의미검색** — 제품 리뷰 요약을 임베딩(1536차원)해 pgvector에 저장 → 사용자 대화도 임베딩 → **코사인 유사도 top-N** 정렬.
4. **LLM 선정** — 위 후보만 LLM이 보고 골라 **추천 이유** 작성. (조건 위반 제품은 LLM이 볼 수조차 없음)
5. **단계적 완화** — 후보가 3개 미만이면 가격 ±1만원 → 제형 → 카테고리 순으로 풀고 *무엇을 풀었는지 정직하게 표기.*

→ 왜 이렇게 만들었는지(전 제품 주입 vs RAG vs 하이브리드 비교)는 **[개발 이력 07](docs/development-history/07-rag-hybrid-recommendation.md)** 참고.

---

## 6. 데이터베이스 모델링 (ERD) *(명세 C)*

```
Django User ─1:1─ UserInfo ─1:1─ SkinProfile
                     │
        ┌────────────┼─────────────┬───────────┬──────────┐
      Like      InUseProduct   Recommendation  Post      Comment/PostLike
        │            │              │1:N        │M2M
        ▼            ▼              ▼            ▼
     Product ◄─────Product   RecommendedProduct─FK─►Product◄─M2M─Post
        ▲
      Review (FK)        Product.embedding = pgvector(1536), Product.form = ArrayField
```

자세한 필드·관계 표는 **[개발 이력 02 · 설계](docs/development-history/02-design.md)** 참고.

---

## 7. 생성형 AI 활용 *(명세 F)*

| 활용 | 내용 |
|---|---|
| 대화 | 사용자 자연어 이해·문답으로 추천 조건 수집 (`gpt-5-nano`) |
| 추천 이유 | 후보 제품에 대한 맞춤 추천 사유 생성 |
| 리뷰 요약 | 수집한 리뷰를 제품별 `ai_summary`·피부타입별 만족도로 가공 |
| 임베딩 | 요약·대화를 1536차원 벡터로 변환(RAG 의미검색의 재료) |

→ [개발 이력 04](docs/development-history/04-data.md) · [06](docs/development-history/06-chatbot-recommendation.md) · [07](docs/development-history/07-rag-hybrid-recommendation.md)

---

## 8. 보안 & 데이터

- **API Key 관리(명세 NF1302)**: 모든 시크릿을 `.env`로 분리, **git에 키 0건 커밋**. (`git ls-files | grep env` → 공개 URL 파일 하나만)
- **인증/인가**: OAuth 2.0 + JWT(access 30분 / refresh 7일 HttpOnly 쿠키, 회전+블랙리스트), 소유권 검사(IDOR 방어), LLM 전용 호출 한도(throttle).
- **데이터(명세 NF1303)**: 올리브영 제품 156종 + AI 요약, `loaddata` 가능한 fixture(`backend/products_seed.json`, `backend/board_seed.json`).

→ [개발 이력 05 · 인증과 보안](docs/development-history/05-auth-security.md)

---

## 9. 실행 방법

### 요구사항
- Python 3.11+ · Node.js 20+ · Docker

### 1) 데이터베이스 (PostgreSQL + pgvector)
```bash
docker compose up -d        # 루트에서: pgvector/pgvector:pg16 컨테이너 기동
```

### 2) 백엔드
```bash
cd backend
cp .env.example .env        # 키·DB 정보 입력 (DJANGO_SECRET_KEY, GMS_API_KEY, OAuth 키, DB_*)
pip install -r requirements.txt
python manage.py migrate
python manage.py loaddata products_seed.json board_seed.json   # 초기 데이터
python manage.py backfill_form                                 # 제형 백필
python manage.py backfill_embeddings                           # 임베딩 적재(RAG)
python manage.py runserver
```

### 3) 프론트엔드
```bash
cd frontend
npm install
npm run dev
```

---

## 10. 명세서 요구사항 충족

명세서 필수 요구사항 9개 + 심화(배포)까지 충족했습니다. 항목별 근거는
**[요구사항 충족 정리](docs/requirements-compliance.md)** 에 한 장으로 정리되어 있습니다.

| F1301 추천 | F1302 API | F1303 커뮤니티 | F1304 RESTful | F1305 배포 | NF1301 Git | NF1302 키관리 | NF1303 데이터 | NF1304 페이지 |
|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|
| ✅ | ✅ | ✅ | ✅ | ✅(심화) | ✅ | ✅ | ✅ | ✅ |

---

## 11. 문서

- 📜 **[개발 이력 (기획→배포→검증)](docs/development-history/README.md)** — 비전공자도 읽는 단계별 정리
- 📊 **[요구사항 충족 정리](docs/requirements-compliance.md)**
- 🎤 **[발표 자료](presentation/README.md)**
- 🗂 [docs 문서 허브](docs/README.md) — 기획·설계·트러블슈팅 원본

> *(제출 시: 명세 1.6에 따라 GitLab 커밋 내역 스크린샷을 이 README 하단 또는 발표자료에 첨부하세요.)*
