# 백엔드 API 구현 보고서 — 찜 / 제품 / 추천 기록 / 회원 탈퇴

> 작성일: 2026-06-22
> 대상: `progress.md`의 남은 백엔드 항목 중 외부 의존성 없이 구현 가능한 기능
> 범위: 제품 조회 API, 찜(Like) API, 추천 기록 API, 회원 탈퇴 API
> 보류: 챗봇 메시지 API · 서버사이드 사용량 제한 (사유는 §6)

이 문서는 "무엇을 만들었나"보다 **"왜 이렇게 만들었나"**에 초점을 둔다.
각 절은 [개념] → [구현] → [왜 이게 정석인가] 순서로 읽으면 된다.

---

## 0. 이번 작업의 큰 그림

기존에 인증/보안(OAuth, JWT, 쿠키)은 끝났지만, 정작 **로그인한 사용자가 할 수 있는 일**
(제품 보기 · 찜하기 · 추천 기록 보기 · 탈퇴하기)이 비어 있었다.
모델(`Product`, `Like`, `Recommendation`, `InUseProduct`)은 이미 정의돼 있었으므로,
이번 작업은 **모델 위에 REST 엔드포인트를 얹는 일**이다.

추가/변경 파일:

| 파일 | 역할 |
|------|------|
| `products/serializers.py` (신규) | 제품·찜 직렬화 |
| `products/views.py` | 제품 목록/상세, 찜 목록/추가/삭제 |
| `products/urls.py` (신규) | products 라우팅 |
| `chat/serializers.py` (신규) | 추천 기록 직렬화 |
| `chat/views.py` | 추천 기록 목록/생성 |
| `chat/urls.py` (신규) | chat 라우팅 |
| `accounts/views.py` | `AccountView` (계정 조회 + 회원 탈퇴), 토큰 갱신 보강 |
| `accounts/urls.py` | `account/` 라우트 추가 |
| `config/urls.py` | products/chat URLConf 포함 |
| `products/tests.py`, `chat/tests.py`, `accounts/tests.py` | 단위 테스트 12종 추가 (총 19종) |

---

## 1. 엔드포인트 요약

| 메서드 | 경로 | 설명 | 인증 |
|--------|------|------|------|
| GET | `/api/v1/products/` | 제품 목록 (페이지네이션, `?category=` 필터) | 필요 |
| GET | `/api/v1/products/<uuid>/` | 제품 상세 | 필요 |
| GET | `/api/v1/likes/` | 내 찜 목록 (제품 정보 포함) | 필요 |
| POST | `/api/v1/likes/` | 찜 추가 `{ "product_id": "<uuid>" }` | 필요 |
| DELETE | `/api/v1/likes/<uuid>/` | 찜 해제 (product_id 기준) | 필요 |
| GET | `/api/v1/recommendations/` | 내 추천 히스토리 (최신순) | 필요 |
| POST | `/api/v1/recommendations/` | 추천 기록 생성 `{ "title": "..." }` | 필요 |
| GET | `/api/v1/account/` | 내 계정 정보 | 필요 |
| DELETE | `/api/v1/account/` | 회원 탈퇴 | 필요 |

---

## 2. 제품 조회 API

### [개념] Serializer와 제네릭 뷰

DRF에서 **Serializer**는 "모델 객체 ↔ JSON" 변환기이자 입력 검증기다.
`ModelSerializer`는 모델 필드를 보고 변환 규칙을 자동 생성해주므로 보일러플레이트가 줄어든다.

**제네릭 뷰**(`ListAPIView`, `RetrieveAPIView`)는 "목록 조회", "단건 조회" 같은
반복되는 CRUD 패턴을 클래스 한 줄로 끝내준다. `queryset` + `serializer_class`만
지정하면 페이지네이션·직렬화·404 처리까지 프레임워크가 담당한다.

### [구현]

```python
class ProductListView(generics.ListAPIView):
    serializer_class = ProductSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        queryset = Product.objects.all().order_by('-review_count', 'name')
        category = self.request.query_params.get('category')
        if category:
            queryset = queryset.filter(category=category)
        return queryset
```

### [왜 이게 정석인가]

- **페이지네이션은 선택이 아니라 기본값이다.** 제품이 수백 건인데 전부 한 응답에
  실으면 응답이 비대해지고 프론트 렌더링도 느려진다. `settings.py`의
  `DEFAULT_PAGINATION_CLASS` + `PAGE_SIZE=10` 덕분에 `ListAPIView`는 자동으로
  `{count, next, previous, results}` 형태로 끊어준다.
- **정렬을 반드시 고정한다.** 정렬이 없는 쿼리셋을 페이지네이션하면
  DB가 매번 다른 순서로 행을 돌려줄 수 있어 2페이지에 1페이지 항목이 다시
  나오거나 누락된다(실제로 DRF가 `UnorderedObjectListWarning`을 띄운다).
  그래서 `-review_count, name`으로 명시적 정렬을 박았다.
- **필터는 `get_queryset()` 오버라이드로.** 쿼리 파라미터 기반 필터는
  이 메서드 안에서 처리하는 것이 DRF 관례다. (규모가 커지면 `django-filter`로 이관)

---

## 3. 찜(Like) API

### [개념] IDOR(Insecure Direct Object Reference)

가장 흔한 권한 취약점. "URL의 ID만 바꾸면 남의 데이터에 접근/조작되는" 문제다.
예: `DELETE /likes/5/` 에서 5가 남의 찜이어도 지워지면 IDOR이다.
방어의 핵심은 **"항상 `request.user` 소유 자원만 대상으로 쿼리한다"**이다.

### [구현]

```python
def post(self, request):
    product = get_object_or_404(Product, pk=product_id)
    like, created = Like.objects.get_or_create(
        user=request.user.userinfo, product=product,
    )
    return Response(LikeSerializer(like).data,
                    status=201 if created else 200)

def delete(self, request, product_id):
    like = Like.objects.filter(
        user=request.user.userinfo, product_id=product_id,
    ).first()
    if not like:
        return Response(status=404)
    like.delete()
    return Response(status=204)
```

### [왜 이게 정석인가]

- **`user`는 절대 클라이언트 입력에서 받지 않는다.** `request.user`(JWT로 검증된
  신뢰 주체)로만 주입한다. 만약 body의 `user_id`를 믿으면 누구나 타인 명의로
  찜을 만들 수 있다 → IDOR. Serializer에서도 `user`를 필드에서 제외해 이중으로 막았다.
- **삭제는 product_id 기준 + 소유자 필터.** 프론트는 "이 제품을 찜했나/안 했나"만
  알면 되므로 like의 PK를 따로 들고 다닐 필요가 없다(토글 UX에 자연스럽다).
  동시에 `filter(user=...)`로 본인 것만 지우게 해 IDOR을 막는다.
- **`get_or_create`로 멱등성 확보.** 더블클릭이나 재요청으로 같은 제품을 두 번
  찜해도 모델의 `UniqueConstraint`가 `IntegrityError(500)`를 던지기 전에
  미리 걸러 200으로 깔끔히 응답한다. (멱등성 = 같은 요청을 여러 번 보내도
  결과가 같음 → 네트워크 재시도에 안전)
- **N+1 쿼리 방지(`select_related`).** 찜 목록을 줄 때 각 찜의 제품을 매번 따로
  조회하면 "찜 1번 + 제품 N번" 쿼리가 나간다. `select_related('product')`로
  JOIN 한 방에 가져와 쿼리 수를 1로 줄였다. 목록 API에서 거의 항상 챙겨야 하는 기본기다.

---

## 4. 추천 기록 API

### [개념] 책임 분리 — 기록 저장과 LLM 생성은 별개다

챗봇이 추천을 "생성"하는 일(LLM 호출)과 그 결과를 "기록/조회"하는 일은
다른 책임이다. LLM 연동은 외부 의존성·비용·인프라가 걸려 있지만,
**기록 CRUD는 지금 당장 독립적으로 제공할 수 있다.**

### [구현]

```python
def post(self, request):
    serializer = RecommendationSerializer(data=request.data)
    if serializer.is_valid():
        serializer.save(user=request.user.userinfo)  # user는 서버가 주입
        return Response(serializer.data, status=201)
    return Response(serializer.errors, status=400)
```

### [왜 이게 정석인가]

- **목록은 항상 `filter(user=request.user...)`로 격리한다.** 추천 기록은
  개인 데이터이므로 다른 사용자 것이 절대 섞이면 안 된다(찜과 동일한 원칙).
- **나중에 붙을 LLM 파이프라인과의 결합도를 낮춘다.** 추천 생성 로직이
  완성되면 그 끝에서 이 API(혹은 내부 함수)를 호출해 기록만 남기면 된다.
  지금 기록 레이어를 먼저 못 박아 두면, LLM 작업과 프론트 히스토리 UI 작업을
  **병렬로** 진행할 수 있다.

---

## 5. 회원 탈퇴 API (가장 신경 쓴 부분)

### [개념 1] CASCADE 연쇄 삭제

`UserInfo.user`는 Django `User`와 `OneToOneField(on_delete=CASCADE)`,
`Like`·`Recommendation`·`InUseProduct`·`SkinProfile`은 `UserInfo`를 FK로
참조하며 역시 CASCADE다. 따라서 **최상위 `User` 하나만 지우면**
그 아래 매달린 모든 개인 데이터가 DB 차원에서 연쇄 삭제된다.
직접 하나하나 지우는 코드를 쓰면 누락·순서 실수가 생기지만, CASCADE는
참조 무결성을 DB가 보장한다.

### [개념 2] 탈퇴 후 토큰 무효화의 함정

직관적으로는 "탈퇴할 때 refresh 토큰을 블랙리스트하면 끝"이라고 생각한다.
그런데 simplejwt의 블랙리스트 레코드(`OutstandingToken`)도 **`User`를 FK로 참조**한다.
즉 `user.delete()`를 하는 순간 블랙리스트 레코드까지 CASCADE로 함께 사라진다.
→ 결과적으로 그 refresh 토큰은 "블랙리스트에 없는" 상태가 되어,
   서명만 유효하면 새 access 토큰을 다시 받아낼 수 있는 **구멍**이 된다.

### [구현]

탈퇴 뷰:

```python
def delete(self, request):
    refresh_token = request.COOKIES.get(REFRESH_COOKIE_NAME)
    if refresh_token:
        try:
            RefreshToken(refresh_token).blacklist()
        except TokenError:
            pass
    request.user.delete()  # CASCADE로 연관 데이터 일괄 삭제
    response = Response(status=204)
    response.delete_cookie(REFRESH_COOKIE_NAME, path=REFRESH_COOKIE_PATH)
    return response
```

토큰 갱신 뷰(보강) — 진짜 방어선:

```python
refresh = RefreshToken(refresh_token)
user_id = refresh.payload.get('user_id')
if not User.objects.filter(pk=user_id, is_active=True).exists():
    raise TokenError('user no longer exists')   # → 401
access = str(refresh.access_token)
```

### [왜 이게 정석인가]

- **블랙리스트만 믿지 않고 "사용자 존재 여부"를 갱신 시점에 재확인한다.**
  위 함정 때문에, 탈퇴/정지된 계정을 막는 신뢰할 수 있는 지점은
  *토큰 발급 순간이 아니라 토큰 사용(갱신) 순간*이다. `is_active=True`까지
  같이 확인하므로 향후 "계정 정지(밴)" 기능에도 그대로 재사용된다.
- **삭제는 비가역 작업이므로 순서를 지킨다.** ①토큰 무효화 → ②계정 삭제 →
  ③쿠키 제거. 쿠키 제거 시 `path`를 설정 때와 동일하게 줘야 브라우저가
  실제로 지운다(쿠키는 name+path가 같아야 삭제됨 — 로그아웃 버그와 같은 원리).
- **테스트로 회귀를 막는다.** `AccountDeleteTest`는 (a) User/UserInfo가 사라지는지,
  (b) 탈퇴한 토큰으로 갱신하면 401인지를 함께 검증한다. 위 함정은 눈으로는
  안 보이고 테스트로만 잡히는 종류의 버그라 특히 중요하다.

---

## 6. 보류한 항목과 그 이유

### 챗봇 메시지 API (`POST /api/v1/chat`)

- **보류 사유:** SSAFY GMS(LLM) 호출 크리덴셜과 RAG 인프라(임베딩 + 벡터 검색)가
  전제다. `plan.md`도 이를 Phase 2(PostgreSQL + pgvector 전환과 동시)로 명시했다.
- **지금 무리하게 만들지 않은 이유:** LLM 키 없이 작성하면 **실행·테스트가 불가능한
  죽은 코드**가 된다. 검증되지 않은 코드를 "완료"로 올리는 것은 기술 부채다.
  대신 추천 "기록" API를 먼저 제공해, LLM이 붙는 순간 결과만 연결하면 되도록 했다.

### 서버사이드 사용량 제한 (일일 N회 카운팅)

- **보류 사유:** 의미 있는 카운팅 대상이 챗봇 호출인데, 그 엔드포인트가 아직 없다.
- **현재 방어 수준:** 전역 DRF Throttling(인증 100/h, 비인증 20/h)이 이미
  적용돼 무차별 호출은 막힌다. 정교한 "일일 한도 + UsageLog 모델"은 챗봇 API와
  함께 구현하는 것이 응집도가 높다.

> 정리: **검증 가능한 것은 지금 끝내고, 외부 의존성이 있는 것은 의존성이
> 준비되는 시점에 함께** 한다. 이것이 무리한 선구현보다 안전한 진행 방식이다.

---

## 7. 테스트 결과

```
Ran 19 tests in 0.043s — OK
```

신규 12종:
- `products`: 찜 추가/멱등/목록(제품정보 포함)/삭제/타인찜삭제차단(IDOR)/인증요구, 제품 페이지네이션/카테고리필터
- `chat`: 추천 생성 / 사용자별 격리 / 인증요구
- `accounts`: 회원 탈퇴(연쇄 삭제 + 탈퇴 후 토큰 갱신 401)

기존 7종(OAuth state/CSRF, 이메일 중복, 토큰 교환·블랙리스트, SkinProfile 검증)은 그대로 유지·통과.
