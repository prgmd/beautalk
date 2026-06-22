from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import Recommendation
from .serializers import RecommendationSerializer


# ──────────────────────────────────────────────
# 추천 기록 (Recommendation history)
# ──────────────────────────────────────────────

class RecommendationListCreateView(APIView):
    """GET  /api/v1/recommendations/  — 내 추천 히스토리 (최신순)
    POST /api/v1/recommendations/  — 추천 기록 생성 (body: {"title": "..."})

    챗봇이 추천을 만들어줄 때마다 그 묶음의 제목/요약을 기록해
    마이페이지에서 과거 추천을 다시 볼 수 있게 한다.
    LLM 연동(챗봇 메시지 API)과 독립적으로, 기록 저장/조회 자체는 먼저 제공한다.
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
            # user는 신뢰할 수 있는 request.user로만 주입 (클라이언트 입력 무시)
            serializer.save(user=request.user.userinfo)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
