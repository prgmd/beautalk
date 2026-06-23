import uuid
from django.db import models

class Product(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    brand = models.CharField(max_length=100)
    name = models.CharField(max_length=100)
    price = models.IntegerField()
    # URLField 기본 max_length=200. 올리브영 추적 파라미터가 붙은 URL은
    # 200자를 초과하므로 넉넉히 확장 (SQLite는 미강제, PostgreSQL은 강제).
    oliveyoung_url = models.URLField(max_length=500)
    image_url = models.URLField(max_length=500)
    category = models.CharField(max_length=50)
    ai_summary = models.TextField(blank=True)
    average_rating = models.FloatField(null=True, blank=True)
    review_count = models.IntegerField(default=0)
    satisfaction_by_type = models.JSONField(default=dict, blank=True)

class Review(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='reviews')
    text = models.TextField()
    rating = models.IntegerField()
    skin_type = models.CharField(max_length=50, blank=True)
    user_name = models.CharField(max_length=100, blank=True)
    recommend_count = models.IntegerField(default=0)
    review_date = models.CharField(max_length=50, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

class Like(models.Model):
    user = models.ForeignKey('accounts.UserInfo', on_delete=models.CASCADE)
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields = ['user', 'product'], name = 'unique_like')
        ]

    # 중복 PK 설정 방법: class Meta 안에 제약조건(constraints) 설정 (여러 개 설정 가능하다)

class InUseProduct(models.Model):
    user = models.ForeignKey('accounts.UserInfo', on_delete=models.CASCADE)
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields = ['user', 'product'], name = 'unique_ln_use')
        ]
