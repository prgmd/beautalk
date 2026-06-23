# RAG 기반 추천 고도화 (pgvector + GMS 임베딩)

> 추천 후보 선정을 **"전 제품을 프롬프트에 욱여넣기" → "대화와 의미적으로 가까운 제품만
> 벡터 검색"** 으로 전환한 작업 정리. API 계약은 그대로라 프론트 영향은 없다.

---

## 1. 배경 — 왜 RAG인가

추천(`POST /api/v1/recommend/`)은 LLM이 "우리 DB에 실제로 있는 제품"만 고르게 해야 한다
(환각 방지). 그래서 제품 목록을 프롬프트에 넣고 "이 중에서 골라"라고 시킨다.

문제는 **무엇을 넣느냐**였다. 처음엔 `ai_summary`가 있는 제품을 **전부** 넣었는데(~27k자),
GMS가 거대한 페이로드를 거부(400)하면서 추천이 깨졌다. 임시로 "리뷰순 30개만"으로 컷했지만,
이건 *대화 내용과 무관하게* 인기 제품을 넣는 것이라 **추천 적합도와 관계없는 후보**가 들어간다.

> **핵심 통찰:** "제품을 다 보여주고 고르게 한다"는 방식은 데이터가 늘수록 반드시 터지고,
> 줄이면 적합도가 떨어진다. 둘 다 피하려면 **"고를 후보 자체를 똑똑하게 추려서" 넣어야 한다.**
> 그게 RAG(Retrieval-Augmented Generation, 검색 증강 생성)다.

## 2. RAG 개념 한 문단

LLM에게 모든 지식을 프롬프트로 떠먹이는 대신, **질문과 관련 있는 조각만 먼저 검색(Retrieval)해
프롬프트에 붙여(Augmented) 생성(Generation)** 시키는 패턴. 검색을 "키워드"가 아니라
**"의미(semantic)"** 로 하려면 텍스트를 숫자 벡터(임베딩)로 바꿔, 벡터 간 거리가 가까운 것을
찾는다. "여드름 자국"과 "진정·재생"이 글자는 달라도 벡터 공간에선 가깝다 — 이게 임베딩의 힘.

## 3. 파이프라인

```
[제품 텍스트] --임베딩--> [1536d 벡터] --저장--> pgvector 컬럼   (오프라인 1회: backfill)
                                                     │
[사용자 대화] --임베딩--> [쿼리 벡터] --코사인 거리 검색--> top-N 후보 제품
                                                     │
                              후보 N개만 프롬프트에 주입 --> LLM이 3개 선택
```

- **오프라인(백필):** 제품 설명을 미리 벡터로 만들어 DB에 저장. 매 추천마다 다시 안 만든다.
- **온라인(추천 시):** 이번 대화만 즉석에서 벡터로 만들어, 저장된 제품 벡터들과 거리 비교.

## 4. 구현 요소

| 구성 | 파일 | 역할 |
|------|------|------|
| 벡터 저장 | `products/models.py` `Product.embedding` | `VectorField(1536)` — pgvector 컬럼 |
| 확장 설치 | `products/migrations/0006_*` | `VectorExtension()` → `CREATE EXTENSION vector` |
| 임베딩 호출 | `chat/embeddings.py` | GMS `/embeddings` 호출 (`text-embedding-3-small`) |
| 백필 | `products/management/commands/backfill_embeddings.py` | 제품 → 벡터 일괄 적재 |
| 검색 | `chat/views.py` `_recommend_candidates()` | 대화 → 쿼리 벡터 → 코사인 top-N |
| 인프라 | `docker-compose.yml` | 이미지 `pgvector/pgvector:pg16` |

### 검색 핵심 코드 (개념)
```python
from pgvector.django import CosineDistance

query_vector = embed_text(대화_텍스트)
Product.objects.exclude(embedding__isnull=True) \
       .order_by(CosineDistance('embedding', query_vector))[:RECOMMEND_POOL_SIZE]
```
`CosineDistance`는 SQL의 pgvector 연산자(`<=>`)로 번역되어 **DB가 직접 거리순 정렬**한다
(파이썬으로 벡터를 다 끌어와 비교하지 않는다 — 그게 pgvector의 존재 이유).

## 5. 폴백 설계 — 왜 항상 후보를 반환하나

`_recommend_candidates()`는 절대 빈손으로 끝나지 않게 설계했다:

1. **임베딩이 하나도 없으면**(백필 전·테스트 환경) → GMS를 부르지 않고 바로 **리뷰순 폴백**.
   → 불필요한 비용·네트워크를 막고, 임베딩이 없는 환경에서도 추천이 동작한다.
2. **임베딩 호출이 실패하면**(GMS 장애) → 예외를 잡아 **리뷰순 폴백**.
   → 외부 의존성 하나가 추천 전체를 멈추지 않게 한다(graceful degradation).

> 이 덕분에 **기존 테스트(임베딩 없는 제품)는 네트워크 호출 없이** 폴백 경로로 그대로 통과한다.

## 6. 설계 결정

- **임베딩 모델:** `text-embedding-3-small` (1536d, 0.001 Credit). 카탈로그 규모엔 충분하고
  10배 비싼 `large`는 과잉. 품질 부족 시 `GMS_EMBED_MODEL` 환경변수로 교체 가능.
- **임베딩 텍스트:** `[카테고리] 브랜드 제품명: ai_summary` — 검색 의미에 기여하는 필드만.
- **임베딩은 seed에 미포함:** 벡터를 dumpdata에 넣으면 seed가 2~3MB로 폭증한다. 제품
  원본에서 **재생성 가능한 파생 데이터**이므로, seed엔 빼고 `backfill_embeddings`로 복원한다.
- **후보 수(`RECOMMEND_POOL_SIZE=15`):** 검색으로 적합한 것만 추리므로 작게 유지(토큰 절약).

## 7. 팀 / 운영 가이드

```bash
# 1) pgvector 이미지로 DB 기동 (기존 postgres_data 볼륨 호환)
docker compose up -d

# 2) 마이그레이션 (CREATE EXTENSION vector + embedding 컬럼)
python manage.py migrate

# 3) 데이터 적재 후 임베딩 백필
python manage.py loaddata products_seed.json
python manage.py backfill_embeddings          # 임베딩 없는 제품만
python manage.py backfill_embeddings --all     # 전체 재생성
```

## 8. 검증

- 전체 테스트 **38개 통과** (기존 34 + RAG 4: 벡터 경로/폴백 경로/임베딩 정렬·빈입력).
- 백필: `ai_summary` 보유 **69건** 임베딩 적재 (전체 156건 중 요약 보유분).
- 수동 스모크: "여드름 자국 진정 토너" 검색 → 스킨케어/토너류가 거리순 반환 확인.

## 9. 남은 것 (후속)

- **LangChain 파이프라인화** — 검색·프롬프트·파싱을 체인으로 구성, 컴포넌트 교체 용이화.
- **LLM 관측/추적** — LangSmith 또는 Langfuse로 프롬프트·토큰·지연·검색결과 추적.
- → RAG 코어가 안정화됐으니 그 위에 얹는 단계.
