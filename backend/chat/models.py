import uuid
from django.db import models


class Recommendation(models.Model):
    """추천 1회 = 배치(부모).

    `/recommend/` 한 번 호출이 Recommendation 1건을 만들고,
    그 밑에 RecommendedProduct(최대 3개)를 매단다.
    title은 배치 요약이며 시리얼라이저에서 외부 키 `content`로 노출한다.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey('accounts.UserInfo', on_delete=models.CASCADE)
    title = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)


class RecommendedProduct(models.Model):
    """배치에 묶인 제품(자식).

    UniqueConstraint를 두지 않는다 — 같은 제품이 다른 날 또 추천되면
    배치(부모)가 다르므로 각각 별도 행으로 남는 '이벤트 로그' 성격이다.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    recommendation = models.ForeignKey(
        Recommendation, on_delete=models.CASCADE, related_name='products',
    )
    product = models.ForeignKey('products.Product', on_delete=models.CASCADE)
    reason = models.TextField(blank=True)  # 제품별 추천 이유
    created_at = models.DateTimeField(auto_now_add=True)
