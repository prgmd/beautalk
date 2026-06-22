from rest_framework import generics, status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from django.shortcuts import get_object_or_404

from .models import Product, Like
from .serializers import ProductSerializer, LikeSerializer


# ──────────────────────────────────────────────
# 제품 조회
# ──────────────────────────────────────────────

class ProductListView(generics.ListAPIView):
    """GET /api/v1/products/  — 제품 목록 (페이지네이션 적용).

    generics.ListAPIView를 쓰면 settings의 DEFAULT_PAGINATION_CLASS가
    자동 적용돼 count/next/previous/results 형태로 응답한다.
    제품 수가 수백 건이므로 전체를 한 번에 내려보내지 않고 페이지 단위로 끊는다.
    """

    serializer_class = ProductSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        # 페이지네이션은 정렬이 고정돼 있어야 페이지 경계에서 항목이 겹치거나
        # 누락되지 않는다. 리뷰 많은(인기) 제품을 앞에 두고 동률은 이름순으로 고정.
        queryset = Product.objects.all().order_by('-review_count', 'name')
        category = self.request.query_params.get('category')
        if category:
            queryset = queryset.filter(category=category)
        return queryset


class ProductDetailView(generics.RetrieveAPIView):
    """GET /api/v1/products/<uuid:pk>/  — 제품 단건 상세."""

    queryset = Product.objects.all()
    serializer_class = ProductSerializer
    permission_classes = [IsAuthenticated]


# ──────────────────────────────────────────────
# 찜 (Like)
# ──────────────────────────────────────────────

class LikeListCreateView(APIView):
    """GET  /api/v1/likes/   — 내가 찜한 제품 목록
    POST /api/v1/likes/   — 찜 추가  (body: {"product_id": "<uuid>"})
    """

    permission_classes = [IsAuthenticated]

    def get(self, request):
        # select_related('product')로 N+1 쿼리를 방지한다.
        # (찜 N개에 대해 제품을 매번 따로 조회하면 1 + N번 쿼리가 나간다)
        likes = (
            Like.objects
            .filter(user=request.user.userinfo)
            .select_related('product')
            .order_by('-created_at')
        )
        return Response(LikeSerializer(likes, many=True).data)

    def post(self, request):
        product_id = request.data.get('product_id')
        if not product_id:
            return Response(
                {'error': 'product_id is required'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        product = get_object_or_404(Product, pk=product_id)

        # get_or_create로 같은 제품을 두 번 찜해도 멱등하게 동작시킨다.
        # (모델의 UniqueConstraint가 최후의 방어선이지만, 여기서 미리 걸러
        #  IntegrityError 500 대신 깔끔한 200을 돌려준다)
        like, created = Like.objects.get_or_create(
            user=request.user.userinfo,
            product=product,
        )
        return Response(
            LikeSerializer(like).data,
            status=status.HTTP_201_CREATED if created else status.HTTP_200_OK,
        )


class LikeDeleteView(APIView):
    """DELETE /api/v1/likes/<uuid:product_id>/  — 찜 해제.

    URL을 product_id 기준으로 잡아 프론트가 like의 PK를 따로 보관할 필요가 없게 했다.
    (사용자는 '이 제품을 찜했다/안 했다'만 알면 되므로 토글 UX와 잘 맞는다)
    """

    permission_classes = [IsAuthenticated]

    def delete(self, request, product_id):
        # 반드시 request.user 소유의 찜만 대상으로 삭제 → 타인 찜 삭제(IDOR) 차단
        like = Like.objects.filter(
            user=request.user.userinfo,
            product_id=product_id,
        ).first()
        if not like:
            return Response(status=status.HTTP_404_NOT_FOUND)

        like.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)
