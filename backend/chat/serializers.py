from rest_framework import serializers

from products.serializers import ProductSerializer
from .models import Recommendation, RecommendedProduct


def product_meets(product, requested) -> dict:
    """제품이 '사용자가 건 제약'을 충족하는지 축별로 평가한다.

    사용자가 건 축만 키로 포함한다(가격 안 보냈으면 price 키 없음).
    완화로 통과한 제품도 '원본 요청(requested)' 기준으로 평가해 정직하게 표시한다.
    (예: 가격은 지켰지만 제형은 미충족 → {'price': True, 'form': False})
    """
    meets = {}
    pmin, pmax = requested.get('price_min'), requested.get('price_max')
    if pmin is not None or pmax is not None:
        ok = True
        if pmin is not None:
            ok = ok and product.price >= pmin
        if pmax is not None:
            ok = ok and product.price <= pmax
        meets['price'] = ok
    if requested.get('forms'):
        meets['form'] = bool(set(product.form) & set(requested['forms']))
    if requested.get('categories'):
        meets['category'] = product.category in requested['categories']
    return meets


class RecommendedProductSerializer(serializers.Serializer):
    """배치에 묶인 제품 1건을 '제품 전체 필드 + reason' 평탄 구조로 내보낸다.

    상세 모달이 실제 ai_summary·평점·만족도를 바로 쓸 수 있도록
    ProductSerializer 전체를 펼친 뒤 reason을 같은 레벨에 덧붙인다.
    context에 'requested'(원본 제약)가 있으면 제약별 충족 여부 meets도 덧붙인다.
    """

    def to_representation(self, instance):
        data = ProductSerializer(instance.product).data
        data['reason'] = instance.reason
        requested = self.context.get('requested')
        if requested:
            data['meets'] = product_meets(instance.product, requested)
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
