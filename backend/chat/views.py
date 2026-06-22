import os

import requests as http
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from accounts.models import SkinProfile
from products.models import Product
from .models import Recommendation
from .serializers import RecommendationSerializer

GMS_API_URL = os.environ.get('GMS_API_URL', 'https://gms.ssafy.io/gmsapi/api.openai.com/v1/chat/completions')
GMS_API_KEY = os.environ.get('GMS_API_KEY')
GMS_MODEL   = os.environ.get('GMS_MODEL', 'gpt-5-nano')


# ──────────────────────────────────────────────
# 챗봇 메시지 API
# ──────────────────────────────────────────────

def _build_system_prompt(user) -> str:
    """사용자 피부 프로필 + 전체 제품 목록을 LLM 시스템 프롬프트로 조립한다.

    프로필 미입력자도 서비스를 쓸 수 있어야 하므로, SkinProfile이 없으면
    프로필 정보를 '미입력'으로 명시하고 일반 추천으로 대응한다.
    """
    # (1) 피부 프로필
    try:
        profile = user.userinfo.skinprofile
        avoid = ', '.join(profile.avoid_ingredients) if profile.avoid_ingredients else '없음'
        concerns = ', '.join(profile.concerns) if profile.concerns else '없음'
        skin_block = (
            f"- 피부 타입: {profile.get_skin_type_display()}\n"
            f"- 피부 고민: {concerns}\n"
            f"- 기피 성분: {avoid}"
        )
    except SkinProfile.DoesNotExist:
        avoid = None
        skin_block = "- 피부 프로필 미입력 (일반 추천으로 대응)"

    # (2) 제품 목록 (ai_summary가 있는 제품만 포함해 토큰 낭비를 줄인다)
    products = Product.objects.exclude(ai_summary='').values(
        'brand', 'name', 'category', 'ai_summary', 'oliveyoung_url'
    )
    product_lines = [
        f"[{p['category']}] {p['brand']} {p['name']}: {p['ai_summary']} | 구매: {p['oliveyoung_url']}"
        for p in products
    ]
    product_block = '\n'.join(product_lines) if product_lines else '(제품 정보 없음)'

    # (3) 기피 성분 지시 (LLM이 확실히 인지하도록 별도 항목으로 강조)
    avoid_instruction = (
        f"\n- 기피 성분({avoid})이 포함된 제품은 절대 추천하지 마세요."
        if avoid and avoid != '없음'
        else ''
    )

    return f"""당신은 화장품 전문 추천 AI 어시스턴트 'Beautalk'입니다.
아래 사용자 피부 프로필과 제품 목록만을 근거로 추천하세요.
화장품·스킨케어와 무관한 질문에는 정중히 거절하고, 다시 화장품 관련 질문을 유도하세요.

[사용자 피부 프로필]
{skin_block}

[추천 가능한 제품 목록]
{product_block}

[규칙]{avoid_instruction}
- 제품을 추천할 때는 브랜드명, 제품명, 추천 이유, 올리브영 링크를 반드시 포함하세요.
- 한 번에 최대 5개까지만 추천하세요.
- 반드시 한국어로 답변하세요."""


class ChatView(APIView):
    """POST /api/v1/chat/

    요청 body:
        {
            "content": "민감성 피부에 좋은 클렌저 추천해줘",
            "history": [
                {"role": "user",      "content": "..."},
                {"role": "assistant", "content": "..."}
            ]
        }

    응답:
        { "content": "AI 답변 텍스트" }

    history는 프론트가 관리하고 매 요청마다 전송한다.
    백엔드는 상태를 저장하지 않는 완전한 Stateless 구조다.
    (상태를 DB에 저장하면 LLM 호출 비용 외에 읽기/쓰기 비용까지 겹치고,
     동시 대화 처리가 복잡해진다. 프론트 메모리 관리가 훨씬 단순하다)
    """

    permission_classes = [IsAuthenticated]

    def post(self, request):
        content = request.data.get('content', '').strip()
        if not content:
            return Response(
                {'error': 'content is required'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # history 검증: role이 user/assistant이고 content가 있는 항목만 통과시킨다.
        # 프론트에서 잘못된 형식이 섞여도 LLM API 오류로 번지지 않도록 방어한다.
        raw_history = request.data.get('history', [])
        history = [
            h for h in raw_history
            if isinstance(h, dict)
            and h.get('role') in ('user', 'assistant')
            and isinstance(h.get('content'), str)
            and h['content'].strip()
        ]

        system_prompt = _build_system_prompt(request.user)

        messages = [{"role": "system", "content": system_prompt}]
        messages.extend(history)
        messages.append({"role": "user", "content": content})

        try:
            res = http.post(
                GMS_API_URL,
                headers={
                    'Authorization': f'Bearer {GMS_API_KEY}',
                    'Content-Type': 'application/json',
                },
                json={'model': GMS_MODEL, 'messages': messages},
                timeout=30,  # LLM 응답은 길어질 수 있으므로 30초
            )
            res.raise_for_status()
        except http.exceptions.Timeout:
            return Response(
                {'error': 'AI 응답 시간 초과. 잠시 후 다시 시도해주세요.'},
                status=status.HTTP_504_GATEWAY_TIMEOUT,
            )
        except http.exceptions.RequestException as exc:
            # 상세 오류를 클라이언트에 노출하지 않는다 (내부 URL/키 정보 유출 방지)
            return Response(
                {'error': 'AI 서버 연결에 실패했습니다. 잠시 후 다시 시도해주세요.'},
                status=status.HTTP_502_BAD_GATEWAY,
            )

        ai_content = res.json()['choices'][0]['message']['content']
        return Response({'content': ai_content})


# ──────────────────────────────────────────────
# 추천 기록 (Recommendation history)
# ──────────────────────────────────────────────

class RecommendationListCreateView(APIView):
    """GET  /api/v1/recommendations/  — 내 추천 히스토리 (최신순)
    POST /api/v1/recommendations/  — 추천 기록 생성 (body: {"title": "..."})
    """

    permission_classes = [IsAuthenticated]

    def get(self, request):
        recommendations = (
            Recommendation.objects
            .filter(user=request.user.userinfo)
            .order_by('-created_at')
        )
        return Response(RecommendationSerializer(recommendations, many=True).data)

    def post(self, request):
        serializer = RecommendationSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save(user=request.user.userinfo)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
