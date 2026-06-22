from rest_framework import serializers

from products.serializers import ProductSerializer
from .models import Recommendation, RecommendedProduct


class RecommendedProductSerializer(serializers.Serializer):
    """배치에 묶인 제품 1건을 '제품 전체 필드 + reason' 평탄 구조로 내보낸다.

    상세 모달이 실제 ai_summary·평점·만족도를 바로 쓸 수 있도록
    ProductSerializer 전체를 펼친 뒤 reason을 같은 레벨에 덧붙인다.
    """

    def to_representation(self, instance):
        data = ProductSerializer(instance.product).data
        data['reason'] = instance.reason
        return data


class RecommendationSerializer(serializers.ModelSerializer):
    """추천 배치 1건. 배치 요약(title)을 외부 키 `content`로 노출하고,
    자식 제품들을 products로 중첩한다.
    """

    content = serializers.CharField(source='title')
    products = RecommendedProductSerializer(many=True, read_only=True)

    class Meta:
        model = Recommendation
        fields = ['id', 'content', 'created_at', 'products']
        read_only_fields = ['id', 'created_at', 'products']
