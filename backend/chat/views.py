import json
import logging
import os
import re

import requests as http
from django.db import transaction
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.throttling import ScopedRateThrottle
from rest_framework.views import APIView

from pgvector.django import CosineDistance

from accounts.models import SkinProfile, UserInfo
from products.models import Product
from .embeddings import embed_text
from .models import Recommendation, RecommendedProduct
from .observability import traceable
from .serializers import RecommendationSerializer

logger = logging.getLogger(__name__)

GMS_API_URL = os.environ.get('GMS_API_URL', 'https://gms.ssafy.io/gmsapi/api.openai.com/v1/chat/completions')
GMS_API_KEY = os.environ.get('GMS_API_KEY')
GMS_MODEL   = os.environ.get('GMS_MODEL', 'gpt-5-nano')

ERR_TIMEOUT = 'AI 응답 시간 초과. 잠시 후 다시 시도해주세요.'
ERR_CONNECT = 'AI 서버 연결에 실패했습니다. 잠시 후 다시 시도해주세요.'

# 추천 프롬프트에 넣을 후보 제품 수. 벡터 검색으로 의미적으로 가까운 것만 추리므로
# 전 제품 주입 없이 작게 유지해도 충분하다(토큰 절약 + 추천 품질).
RECOMMEND_POOL_SIZE = 15
RECOMMEND_SUMMARY_LIMIT = 150

# 하이브리드 필터 — 후보가 이 수 미만이면 제약을 단계적으로 완화한다.
# 추천은 3개라 후보 ≥3이면 답을 만들 수 있어, 3 미만일 때만 완화(조건 위반 최소화).
MIN_POOL = 3
PRICE_RELAX = 10000  # 완화 1단계: 가격대 ±1만원 확장

# 사용자 발화에서 제형 의도를 뽑을 키워드. backfill_form의 제품명 규칙과 키셋은 같지만,
# 여기선 '사용자 요청 문장'을 파싱한다(브라켓·카테고리 폴백 없음).
_SUN_KEYWORDS = ['선크림', '썬크림', '선세럼', '선블록', '선스틱', '선스크린', '썬스크린', '자차']
_FORM_KEYWORDS = [
    ('toner', ['토너', '스킨']),
    ('lotion', ['로션', '에멀전', '유액']),
    ('essence', ['에센스']),
    ('serum', ['세럼', '앰플']),
    ('cream', ['크림']),
    ('mist', ['미스트']),
    ('pad', ['패드']),
    ('mask', ['마스크', '팩']),
]


# ──────────────────────────────────────────────
# 공통 — GMS 호출 + 프롬프트 조립
# ──────────────────────────────────────────────

def _skin_block(user) -> str:
    """사용자 피부 프로필을 프롬프트용 텍스트로 만든다.

    프로필 미입력자도 서비스를 쓸 수 있어야 하므로, 없으면 '미입력'으로 명시한다.
    (기피 성분 필터는 이번 범위 밖이라 avoid_ingredients는 참고용으로만 노출한다)
    """
    try:
        profile = user.userinfo.skinprofile
    except (SkinProfile.DoesNotExist, UserInfo.DoesNotExist, AttributeError):
        # 프로필 미입력은 물론, UserInfo가 아직 없는 사용자도 500 대신 일반 추천으로 흡수
        return '- 피부 프로필 미입력 (일반 추천으로 대응)'

    concerns = ', '.join(profile.concerns) if profile.concerns else '없음'
    avoid = ', '.join(profile.avoid_ingredients) if profile.avoid_ingredients else '없음'
    return (
        f"- 피부 타입: {profile.get_skin_type_display()}\n"
        f"- 피부 고민: {concerns}\n"
        f"- 기피 성분: {avoid}"
    )


@traceable(name='gms_call')
def _call_gms(messages, *, timeout=60):
    """GMS Chat Completions 호출. 성공 시 message content 문자열을 반환한다.

    실패는 (None, error_response) 형태로 돌려준다. 호출 측에서 그대로 return.
    """
    payload = {'model': GMS_MODEL, 'messages': messages}

    # 한글이 섞인 payload를 명시적으로 UTF-8로 인코딩 (서버 기본 인코딩에 의존하지 않음)
    payload_json = json.dumps(payload, ensure_ascii=False).encode('utf-8')

    try:
        res = http.post(
            GMS_API_URL,
            headers={
                'Authorization': f'Bearer {GMS_API_KEY}',
                'Content-Type': 'application/json; charset=utf-8',
            },
            data=payload_json,
            timeout=timeout,
        )
        res.raise_for_status()
    except http.exceptions.Timeout:
        logger.warning('GMS 응답 시간 초과 (timeout=%ss)', timeout)
        return None, Response({'error': ERR_TIMEOUT}, status=status.HTTP_504_GATEWAY_TIMEOUT)
    except http.exceptions.RequestException as e:
        logger.error('GMS 호출 실패: %s', e)
        return None, Response({'error': ERR_CONNECT}, status=status.HTTP_502_BAD_GATEWAY)

    # 예상치 못한 200 페이로드(스키마 변형)도 KeyError/500로 새지 않게 502로 방어
    try:
        return res.json()['choices'][0]['message']['content'], None
    except (KeyError, IndexError, TypeError, ValueError) as e:
        logger.error('GMS 응답 파싱 실패: %s', e)
        return None, Response({'error': ERR_CONNECT}, status=status.HTTP_502_BAD_GATEWAY)


def _clean_history(raw_history):
    """role이 user/assistant이고 content가 있는 항목만 통과시킨다.

    프론트에서 잘못된 형식이 섞여도 LLM API 오류로 번지지 않도록 방어한다.
    """
    return [
        h for h in raw_history
        if isinstance(h, dict)
        and h.get('role') in ('user', 'assistant')
        and isinstance(h.get('content'), str)
        and h['content'].strip()
    ]


# ──────────────────────────────────────────────
# 대화 — POST /api/v1/chat/
# ──────────────────────────────────────────────

def _availability_hint(history) -> str:
    """현재 대화의 제약으로 실제 재고를 SQL로 읽어 한 줄 요약한다 (라이브 그라운딩).

    임베딩 없이 제약 추출(_resolve_constraints)+필터(_filtered_qs)를 재활용해, 봇이
    "데이터에 실제로 뭐가 있는지"에 근거해 대화하게 한다(freestyle 방지). 제약이 하나도
    없으면 빈 문자열(주입 안 함). 비용은 가벼운 count + min/max 쿼리뿐.
    """
    c = _resolve_constraints(history, None)
    if not (c['forms'] or c['price_min'] is not None
            or c['price_max'] is not None or c['categories']):
        return ''

    qs = _filtered_qs(Product.objects.exclude(ai_summary=''), c)
    n = qs.count()
    if n == 0:
        return ('현재까지 파악된 조건에 맞는 제품이 0개입니다. '
                '조건(가격대·제형)을 넓히도록 자연스럽게 유도하세요.')
    prices = list(qs.values_list('price', flat=True))
    return (f'현재 조건에 맞는 제품 약 {n}개 (가격 {min(prices):,}~{max(prices):,}원). '
            f'충분하면 더 캐묻지 말고 추천으로 넘기세요.')


def _build_chat_prompt(user, availability='') -> str:
    """대화 단계 시스템 프롬프트.

    추천이 실제로 쓸 수 있는 축(제품군·제형·가격대·피부고민)에만 대화를 묶는다(grounding).
    데이터에 없는 속성(향료·성분·세부 텍스처·SPF 수치)은 묻지 않게 하고, '모름/상관없음'을
    유효한 답으로 수용해 같은 질문으로 빙빙 도는 것을 막는다.
    availability(현재 조건의 실제 재고 현황)가 있으면 주입해 데이터에 근거해 대화하게 한다.
    """
    categories = list(
        Product.objects.values_list('category', flat=True).distinct()
    )
    category_block = ', '.join(c for c in categories if c) or '(제품 정보 없음)'
    form_block = ', '.join(label for _, label in Product.FORM_CHOICES)
    availability_block = f'\n[현재 데이터 현황 — 근거로 삼으세요]\n{availability}\n' if availability else ''

    return f"""당신은 화장품 추천 상담 AI 'Beautalk'입니다.
사용자와 짧게 대화하며 추천에 필요한 정보를 모읍니다.

[사용자 피부 프로필]
{_skin_block(user)}

[추천에 쓰는 정보 — 이 안에서만 질문하세요]
- 제품군(카테고리): {category_block}
- 제형(원하면): {form_block}
- 가격대(원하면): "2~3만원대", "2만원 이하" 같은 범위
- 피부 고민: 위 프로필 참고 (없으면 한 번만 물어볼 수 있음)
{availability_block}

[절대 묻지 말 것 — 데이터에 없어 추천에 못 씀]
- 향료/성분 포함 여부, 세부 텍스처(젤·스틱 등 제형 하위 구분), SPF 정확한 수치.
- 이런 건 시스템이 거를 수 없으니 묻지 마세요. 사용자에게 "성분표를 확인하라"고 시키지 마세요.

[대화 규칙]
- 답변은 최대 2문장으로 짧게. 한 번에 한 가지만 물어보세요.
- 사용자가 "모름/상관없음/적당히/아무거나"라고 하면 그것도 유효한 답입니다.
  그 항목은 더 캐묻지 말고 넘어가세요. 같은 질문을 표현만 바꿔 반복하지 마세요.
- 이미 답을 들은 항목은 다시 묻지 마세요.
- 어려운 전문 용어 대신 쉬운 말로 설명하고, 용어부터 먼저 묻지 마세요.
- 제품을 직접 나열/추천하지 마세요. 추천은 별도 단계에서 처리됩니다.
- 화장품·스킨케어와 무관한 질문은 정중히 거절하고 다시 유도하세요.
- 반드시 한국어로 답하세요.

[출력 형식]
반드시 아래 JSON 형식으로만 답하세요:
{{"content": "2문장 이내의 짧은 답변", "ready": true 또는 false}}
- content: 채팅에 표시할 대화 답변 (2문장 이내, 제품 나열 금지)
- ready: 원하는 제품군(또는 제형)이 특정되면 true. 가격·고민은 있으면 좋지만 필수 아님.
  정보가 충분하면 더 묻지 말고 ready=true로 추천 단계에 넘기세요."""


class ChatView(APIView):
    """POST /api/v1/chat/  — 대화 단계 (Stateless)

    요청: { "content": "...", "history": [{role, content}, ...] }
    응답: { "content": "AI 답변", "ready": false }

    history는 프론트가 관리하고 매 요청마다 전송한다(백엔드는 상태 저장 안 함).
    """

    permission_classes = [IsAuthenticated]
    throttle_classes = [ScopedRateThrottle]
    throttle_scope = 'chat'  # 대화는 다발성 → 넉넉한 한도 (운영 100/day, DEBUG 무제한)

    def post(self, request):
        content = request.data.get('content', '').strip()
        if not content:
            return Response({'error': 'content is required'}, status=status.HTTP_400_BAD_REQUEST)

        history = _clean_history(request.data.get('history', []))

        # 방금 보낸 content까지 포함해 현재 제약의 실제 재고를 읽어 프롬프트에 주입(라이브 그라운딩).
        availability = _availability_hint(history + [{'role': 'user', 'content': content}])
        messages = [{'role': 'system', 'content': _build_chat_prompt(request.user, availability)}]
        messages.extend(history)
        messages.append({'role': 'user', 'content': content})

        raw, error = _call_gms(messages)
        if error:
            return error

        # LLM이 JSON을 못 지킨 경우, 전체 텍스트를 답변으로 쓰고 ready=false로 안전 처리
        try:
            parsed = json.loads(raw)
            ai_content = (parsed.get('content') or '').strip()
            ready = bool(parsed.get('ready', False))
            if not ai_content:
                ai_content, ready = raw, False
        except (json.JSONDecodeError, TypeError, AttributeError):
            ai_content, ready = raw, False

        return Response({'content': ai_content, 'ready': ready})


# ──────────────────────────────────────────────
# 추천 — POST /api/v1/recommend/
# ──────────────────────────────────────────────

# ── 제약 추출 (규칙 기반) ────────────────────────────────
# 자연어 발화 → 구조화 제약. 규칙으로 못 잡으면 빈손 → 필터 없이 폴백(fail-open).

# "N만", "N천", "N만M천" 조합을 원으로. 둘 다 없으면 None.
_PRICE_TOKEN = r'(?:(\d+)만)?(?:(\d+)천)?원'


def _won(man, cheon):
    return (int(man) if man else 0) * 10000 + (int(cheon) if cheon else 0) * 1000


def _extract_price(text: str):
    """발화에서 가격 하한/상한(원)을 추출한다. 만원·천원·"N만M천원"을 지원. 못 잡으면 (None, None)."""
    t = text.replace(',', '').replace(' ', '')
    m = re.search(r'(\d+)[~\-](\d+)만원', t)               # "2~3만원"
    if m:
        return int(m.group(1)) * 10000, int(m.group(2)) * 10000
    m = re.search(r'(\d+)[~\-](\d+)천원', t)               # "5~8천원"
    if m:
        return int(m.group(1)) * 1000, int(m.group(2)) * 1000
    m = re.search(r'(\d+)만원대', t)                       # "3만원대" → 3.0~3.9만
    if m:
        base = int(m.group(1)) * 10000
        return base, base + 9999
    m = re.search(_PRICE_TOKEN + r'(이하|미만|아래|안쪽|이내)', t)   # "2만5천원 이하"
    if m and (m.group(1) or m.group(2)):
        return None, _won(m.group(1), m.group(2))
    m = re.search(_PRICE_TOKEN + r'(이상|초과|넘|부터)', t)
    if m and (m.group(1) or m.group(2)):
        return _won(m.group(1), m.group(2)), None
    return None, None


def _extract_forms(text: str) -> list:
    """발화에서 제형 키 리스트를 추출한다. 선크림류를 먼저 처리해 '크림' 오인을 막는다."""
    t = text.replace(' ', '').replace('스킨케어', '').lower()  # '스킨케어'는 토너(스킨) 오인 방지
    forms = []
    if any(k in t for k in _SUN_KEYWORDS):
        forms.append('suncream')
        for k in _SUN_KEYWORDS:
            t = t.replace(k, '')   # 선크림류 제거 후 '크림/세럼' 가산 매칭
    if any(k in t for k in ['클렌저', '클렌징', '클렌즈']):
        forms.append('cleanser')
    for form, keywords in _FORM_KEYWORDS:
        if form not in forms and any(k in t for k in keywords):
            forms.append(form)
    return forms


@traceable(name='resolve_constraints')
def _resolve_constraints(history, filters) -> dict:
    """제약을 확정한다. 명시 filters가 추출값보다 우선하고, 빈 축만 발화 추출로 보강한다.
    enum 밖 form·뒤집힌 가격은 버린다(검증; 잘못된 추출이 엉뚱한 필터를 만들지 않게).
    """
    text = ' '.join(h['content'] for h in history if h.get('role') == 'user')
    pmin, pmax = _extract_price(text)
    ex = {'forms': _extract_forms(text), 'price_min': pmin, 'price_max': pmax, 'categories': []}

    f = filters or {}
    valid_forms = {k for k, _ in Product.FORM_CHOICES}
    out = {
        'forms': [x for x in (f.get('forms') or ex['forms']) if x in valid_forms],
        'price_min': f.get('price_min') if f.get('price_min') is not None else ex['price_min'],
        'price_max': f.get('price_max') if f.get('price_max') is not None else ex['price_max'],
        'categories': list(f.get('categories') or ex['categories']),
    }
    # 가격이 뒤집혔으면(min>max) 둘 다 버림 — 잘못된 입력으로 0건 만들지 않게.
    if out['price_min'] is not None and out['price_max'] is not None \
            and out['price_min'] > out['price_max']:
        out['price_min'] = out['price_max'] = None
    return out


# ── SQL 필터 + 단계적 완화 ───────────────────────────────

def _filtered_qs(base, c):
    """제약 dict로 QuerySet을 거른다. 보낸 축만 적용."""
    qs = base
    if c.get('price_min') is not None:
        qs = qs.filter(price__gte=c['price_min'])
    if c.get('price_max') is not None:
        qs = qs.filter(price__lte=c['price_max'])
    if c.get('forms'):
        qs = qs.filter(form__overlap=c['forms'])   # 요청 제형과 교집합(OR 매칭)
    if c.get('categories'):
        qs = qs.filter(category__in=c['categories'])
    return qs


def _apply_degradation(base, requested):
    """후보가 MIN_POOL 미만이면 가격확장→제형해제→카테고리해제 순으로 완화한다.
    반환: (필터된 QuerySet, 실제 적용된 제약 applied, 완화한 축 리스트 relaxed_axes).
    """
    applied = dict(requested)
    relaxed = []

    def enough(c):
        return _filtered_qs(base, c).count() >= MIN_POOL

    if enough(applied):
        return _filtered_qs(base, applied), applied, relaxed

    # 1) 가격대 ±확장 (예산 최대한 존중)
    if applied.get('price_min') is not None or applied.get('price_max') is not None:
        applied = dict(applied)
        if applied.get('price_min') is not None:
            applied['price_min'] = max(0, applied['price_min'] - PRICE_RELAX)
        if applied.get('price_max') is not None:
            applied['price_max'] += PRICE_RELAX
        relaxed.append('price')
        if enough(applied):
            return _filtered_qs(base, applied), applied, relaxed

    # 2) 제형 해제
    if applied.get('forms'):
        applied = dict(applied, forms=[])
        relaxed.append('form')
        if enough(applied):
            return _filtered_qs(base, applied), applied, relaxed

    # 3) 카테고리 해제
    if applied.get('categories'):
        applied = dict(applied, categories=[])
        relaxed.append('category')

    # 다 풀어도 부족할 수 있으나(작은 DB) 있는 만큼 반환 — 추천이 멈추지 않게.
    return _filtered_qs(base, applied), applied, relaxed


def _rank_candidates(qs, history):
    """필터된 후보를 대화 임베딩 코사인순으로 정렬한다. 임베딩 없거나 실패 시 리뷰순 폴백."""
    embedded = qs.exclude(embedding__isnull=True)
    if embedded.exists():
        query_text = ' '.join(
            h['content'] for h in history if h.get('role') == 'user'
        ).strip() or '화장품 추천'
        try:
            query_vector = embed_text(query_text)
            return list(
                embedded.order_by(CosineDistance('embedding', query_vector))[:RECOMMEND_POOL_SIZE]
            )
        except Exception as e:
            logger.warning('임베딩 검색 실패, 리뷰순 폴백: %s', e)
    return list(qs.order_by('-review_count')[:RECOMMEND_POOL_SIZE])


@traceable(name='recommend_candidates')
def _recommend_candidates(history, filters=None):
    """대화(+선택적 filters)로 추천 후보를 추린다 — 하이브리드 검색의 핵심.

    ① 제약 추출(규칙) → ② SQL 필터(가격/제형/카테고리) → ③ 부족하면 단계적 완화
    → ④ 걸러진 후보를 임베딩 코사인순 정렬. 하드 제약은 SQL이 거르므로 LLM은 위반
    제품을 볼 수조차 없다(정형 제약 보장). 의미적 미세 정렬만 임베딩이 맡는다.

    반환: (후보 리스트, constraints 메타). 메타는 응답의 완화 배너·충족 배지에 쓰인다.
    """
    requested = _resolve_constraints(history, filters)
    base = Product.objects.exclude(ai_summary='')
    qs, applied, relaxed_axes = _apply_degradation(base, requested)
    candidates = _rank_candidates(qs, history)

    constraints = {
        'requested': requested,
        'applied': applied,
        'relaxed': bool(relaxed_axes),
        'relaxed_axes': relaxed_axes,
    }
    return candidates, constraints


def _relaxation_note(relaxed_axes) -> str:
    """완화한 축을 사용자에게 알리는 안내문(템플릿). 완화 없으면 빈 문자열."""
    if not relaxed_axes:
        return ''
    labels = {'price': '가격대', 'form': '제형', 'category': '카테고리'}
    axes = '·'.join(labels[a] for a in relaxed_axes if a in labels)
    return f'요청하신 조건({axes})에 딱 맞는 제품이 부족해, 해당 조건을 완화해 비슷한 제품으로 추천드려요.'


def _build_recommend_prompt(user, products) -> str:
    """추천 단계 시스템 프롬프트. 검색으로 추린 후보 제품을 id와 함께 제시하고,
    LLM이 그 목록의 '정확한 id 3개'를 고르도록 강제한다(환각 방지).
    """
    product_lines = [
        f"id={p.id} | [{p.category}] {p.brand} {p.name} | "
        f"{p.price:,}원 | 제형:{'/'.join(p.form) or '-'}: "
        f"{p.ai_summary[:RECOMMEND_SUMMARY_LIMIT]}"
        for p in products
    ]
    product_block = '\n'.join(product_lines) if product_lines else '(제품 정보 없음)'

    return f"""당신은 화장품 추천 AI 'Beautalk'입니다.
지금까지의 대화와 사용자 피부 프로필을 근거로 아래 제품 목록에서 가장 알맞은 3개를 고르세요.

[사용자 피부 프로필]
{_skin_block(user)}

[추천 가능한 제품 목록]
{product_block}

[규칙]
- 반드시 위 목록에 있는 id만 사용하세요. 목록에 없는 제품을 지어내지 마세요.
- 정확히 3개를 고르세요(목록이 3개 미만이면 있는 만큼).
- 각 제품마다 사용자 맞춤 추천 이유를 한국어로 작성하세요.

[출력 형식]
반드시 아래 JSON 형식으로만 답하세요:
{{"content": "추천 묶음 전체 요약 한두 문장", "products": [{{"id": "제품 id", "reason": "추천 이유"}}, ...]}}"""


class RecommendView(APIView):
    """POST /api/v1/recommend/  — 추천 단계 (배치 생성)

    요청: { "history": [{role, content}, ...] }
    응답: { "id", "content", "created_at", "products": [제품 전체 필드 + reason, ...] }

    LLM이 고른 id를 DB로 검증해 실제 제품만 반환하고, Recommendation(배치) 1건 +
    RecommendedProduct(자식)를 저장한다.
    """

    permission_classes = [IsAuthenticated]
    throttle_classes = [ScopedRateThrottle]
    throttle_scope = 'recommend'  # 배치 생성은 드물고 무거움 → 빡빡한 한도 (운영 20/day, DEBUG 무제한)

    def post(self, request):
        history = _clean_history(request.data.get('history', []))

        candidates, constraints = _recommend_candidates(history, request.data.get('filters'))
        messages = [{'role': 'system', 'content': _build_recommend_prompt(request.user, candidates)}]
        messages.extend(history)
        messages.append({'role': 'user', 'content': '지금까지의 대화를 바탕으로 제품을 추천해줘.'})

        raw, error = _call_gms(messages)
        if error:
            return error

        try:
            parsed = json.loads(raw)
            summary = (parsed.get('content') or '').strip()
            picks = parsed.get('products', [])
            if not isinstance(picks, list):
                raise ValueError
        except (json.JSONDecodeError, TypeError, AttributeError, ValueError):
            logger.warning('추천 응답 JSON 파싱 실패: %.200s', raw)
            return Response({'error': ERR_CONNECT}, status=status.HTTP_502_BAD_GATEWAY)

        # LLM이 고른 id를 DB로 검증 (환각/오타 제거). LLM 순서를 유지하고 중복은 제거한다.
        id_to_reason = {}
        for p in picks:
            if isinstance(p, dict) and p.get('id') and str(p['id']) not in id_to_reason:
                id_to_reason[str(p['id'])] = (p.get('reason') or '').strip()

        product_map = {str(prod.id): prod for prod in Product.objects.filter(id__in=id_to_reason.keys())}
        matched = [(product_map[pid], reason) for pid, reason in id_to_reason.items() if pid in product_map]
        matched = matched[:3]  # LLM이 3개를 초과해 줘도 상한 적용 (프롬프트 규칙 강제)

        if not matched:
            # 유효한 제품을 하나도 못 골랐으면 빈 배치를 남기지 않고 재시도를 유도한다
            logger.warning('추천 결과에 유효한 제품 없음 (id 검증 후 0개)')
            return Response({'error': ERR_CONNECT}, status=status.HTTP_502_BAD_GATEWAY)

        with transaction.atomic():
            batch = Recommendation.objects.create(user=request.user.userinfo, title=summary)
            RecommendedProduct.objects.bulk_create([
                RecommendedProduct(recommendation=batch, product=prod, reason=reason)
                for prod, reason in matched
            ])

        # products 정렬을 LLM 선택 순서대로 보장하기 위해 prefetch 대신 재조회 후 직렬화
        batch = (
            Recommendation.objects
            .prefetch_related('products__product')
            .get(pk=batch.pk)
        )
        # 원본 제약을 context로 넘겨 제품별 meets를 함께 직렬화한다.
        data = RecommendationSerializer(
            batch, context={'requested': constraints['requested']}
        ).data
        # 완화 메타(constraints)를 가산적으로 덧붙인다 — 없으면 FE는 배너 미표시.
        data['constraints'] = dict(constraints, note=_relaxation_note(constraints['relaxed_axes']))
        return Response(data, status=status.HTTP_201_CREATED)


# ──────────────────────────────────────────────
# 추천 히스토리 — GET /api/v1/recommendations/
# ──────────────────────────────────────────────

class RecommendationListView(APIView):
    """GET /api/v1/recommendations/  — 내 추천 히스토리 (배치 단위, 최신순)"""

    permission_classes = [IsAuthenticated]

    def get(self, request):
        recommendations = (
            Recommendation.objects
            .filter(user=request.user.userinfo)
            .prefetch_related('products__product')
            .order_by('-created_at')
        )
        return Response(RecommendationSerializer(recommendations, many=True).data)
