from rest_framework import serializers

from .models import Product, Like


class ProductSerializer(serializers.ModelSerializer):
    """제품 한 건을 클라이언트로 내보내는 직렬화기.

    크롤링으로 수집된 모든 표시용 필드를 그대로 노출한다.
    추천 카드·찜 목록·제품 상세에서 공통으로 재사용한다.
    """

    class Meta:
        model = Product
        fields = [
            'id', 'brand', 'name', 'price',
            'oliveyoung_url', 'image_url', 'category',
            'ai_summary', 'average_rating', 'review_count',
            'satisfaction_by_type',
        ]


class LikeSerializer(serializers.ModelSerializer):
    """찜 1건. 목록 응답에서 바로 제품 정보를 보여줄 수 있도록 product를 중첩 직렬화한다.

    user는 요청자(request.user)로 서버에서 강제 주입하므로 입력으로 받지 않는다.
    (클라이언트가 user를 지정하게 두면 타인 명의 찜을 만들 수 있는 IDOR 취약점이 된다)
    """

    product = ProductSerializer(read_only=True)

    class Meta:
        model = Like
        fields = ['id', 'product', 'created_at']
        read_only_fields = ['id', 'created_at']
