import json
import os

import requests as http
from django.db import transaction
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from accounts.models import SkinProfile
from products.models import Product
from .models import Recommendation, RecommendedProduct
from .serializers import RecommendationSerializer

GMS_API_URL = os.environ.get('GMS_API_URL', 'https://gms.ssafy.io/gmsapi/api.openai.com/v1/chat/completions')
GMS_API_KEY = os.environ.get('GMS_API_KEY')
GMS_MODEL   = os.environ.get('GMS_MODEL', 'gpt-5-nano')

ERR_TIMEOUT = 'AI 응답 시간 초과. 잠시 후 다시 시도해주세요.'
ERR_CONNECT = 'AI 서버 연결에 실패했습니다. 잠시 후 다시 시도해주세요.'


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
    except SkinProfile.DoesNotExist:
        return '- 피부 프로필 미입력 (일반 추천으로 대응)'

    concerns = ', '.join(profile.concerns) if profile.concerns else '없음'
    avoid = ', '.join(profile.avoid_ingredients) if profile.avoid_ingredients else '없음'
    return (
        f"- 피부 타입: {profile.get_skin_type_display()}\n"
        f"- 피부 고민: {concerns}\n"
        f"- 기피 성분: {avoid}"
    )


def _call_gms(messages, *, timeout=30):
    """GMS Chat Completions 호출. 성공 시 message content 문자열을 반환한다.

    실패는 (None, error_response) 형태로 돌려준다. 호출 측에서 그대로 return.
    """
    payload = {'model': GMS_MODEL, 'messages': messages}

    try:
        res = http.post(
            GMS_API_URL,
            headers={
                'Authorization': f'Bearer {GMS_API_KEY}',
                'Content-Type': 'application/json',
            },
            json=payload,
            timeout=timeout,
        )
        res.raise_for_status()
    except http.exceptions.Timeout:
        return None, Response({'error': ERR_TIMEOUT}, status=status.HTTP_504_GATEWAY_TIMEOUT)
    except http.exceptions.RequestException:
        # 내부 URL/키 유출 방지를 위해 상세 오류는 노출하지 않는다
        return None, Response({'error': ERR_CONNECT}, status=status.HTTP_502_BAD_GATEWAY)

    return res.json()['choices'][0]['message']['content'], None


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

def _build_chat_prompt(user) -> str:
    """대화 단계 시스템 프롬프트. 한두 문장씩 짧게 답하면서 추천에 필요한
    정보(원하는 제품군·향/가격대 선호 등)를 하나씩 물어본다.
    """
    categories = list(
        Product.objects.values_list('category', flat=True).distinct()
    )
    category_block = ', '.join(c for c in categories if c) or '(제품 정보 없음)'

    return f"""당신은 화장품 추천 상담 AI 'Beautalk'입니다.
사용자 질문에 최대 2문장으로 짧게 답하고, 필요한 정보는 하나씩 물어보세요.

[사용자 피부 프로필]
{_skin_block(user)}

[취급 제품군]
{category_block}

[대화 규칙]
- 답변은 최대 2문장 (2-3줄)으로 짧게.
- 한 번에 한 가지만 물어보세요.
- 제품을 직접 나열/추천하지 마세요. 추천은 별도 단계에서 처리됩니다.
- 화장품·스킨케어와 무관한 질문은 정중히 거절하고 다시 유도하세요.
- 반드시 한국어로 답하세요.

[출력 형식]
반드시 아래 JSON 형식으로만 답하세요:
{{"content": "2문장 이내의 짧은 답변", "ready": true 또는 false}}
- content: 채팅에 표시할 대화 답변 (2문장 이내, 제품 나열 금지)
- ready: 추천을 의미 있게 할 만큼 정보(특히 원하는 제품군)가 모였으면 true, 아니면 false"""


class ChatView(APIView):
    """POST /api/v1/chat/  — 대화 단계 (Stateless)

    요청: { "content": "...", "history": [{role, content}, ...] }
    응답: { "content": "AI 답변", "ready": false }

    history는 프론트가 관리하고 매 요청마다 전송한다(백엔드는 상태 저장 안 함).
    """

    permission_classes = [IsAuthenticated]

    def post(self, request):
        content = request.data.get('content', '').strip()
        if not content:
            return Response({'error': 'content is required'}, status=status.HTTP_400_BAD_REQUEST)

        history = _clean_history(request.data.get('history', []))

        messages = [{'role': 'system', 'content': _build_chat_prompt(request.user)}]
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

def _build_recommend_prompt(user) -> str:
    """추천 단계 시스템 프롬프트. 제품 목록을 id와 함께 제시하고,
    LLM이 그 목록의 '정확한 id 3개'를 고르도록 강제한다(환각 방지).
    """
    products = Product.objects.exclude(ai_summary='').values(
        'id', 'brand', 'name', 'category', 'ai_summary',
    )
    product_lines = [
        f"id={p['id']} | [{p['category']}] {p['brand']} {p['name']}: {p['ai_summary']}"
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

    def post(self, request):
        history = _clean_history(request.data.get('history', []))

        messages = [{'role': 'system', 'content': _build_recommend_prompt(request.user)}]
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
        except (json.JSONDecodeError, TypeError, AttributeError, ValueError) as e:
            import sys
            print(f'[RECOMMEND DEBUG] JSON 파싱 실패: {type(e).__name__}: {e}', file=sys.stderr)
            print(f'[RECOMMEND DEBUG] 원본 응답: {raw[:200]}', file=sys.stderr)
            return Response({'error': ERR_CONNECT}, status=status.HTTP_502_BAD_GATEWAY)

        # LLM이 고른 id를 DB로 검증 (환각/오타 제거). LLM 순서를 유지하고 중복은 제거한다.
        id_to_reason = {}
        for p in picks:
            if isinstance(p, dict) and p.get('id') and p['id'] not in id_to_reason:
                id_to_reason[str(p['id'])] = (p.get('reason') or '').strip()

        product_map = {str(prod.id): prod for prod in Product.objects.filter(id__in=id_to_reason.keys())}
        matched = [(product_map[pid], reason) for pid, reason in id_to_reason.items() if pid in product_map]

        if not matched:
            # 유효한 제품을 하나도 못 골랐으면 빈 배치를 남기지 않고 재시도를 유도한다
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
        return Response(RecommendationSerializer(batch).data, status=status.HTTP_201_CREATED)


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
