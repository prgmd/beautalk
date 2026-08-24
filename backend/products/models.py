import uuid
from django.contrib.postgres.fields import ArrayField
from django.db import models
from pgvector.django import VectorField

class Product(models.Model):
    # 제형(form) enum — 하이브리드 추천의 SQL 필터 축.
    # 백필·검증·시리얼라이저가 같은 정의를 공유하도록 모델에 단일 출처로 둔다.
    # (key=영문 enum, label=FE 칩 한글 라벨. docs/recommend-hybrid-contract.md §4와 일치)
    FORM_CHOICES = [
        ('toner', '스킨/토너'),
        ('lotion', '로션/에멀전'),
        ('essence', '에센스'),
        ('serum', '세럼/앰플'),
        ('cream', '크림'),
        ('mist', '미스트'),
        ('suncream', '선크림'),
        ('cleanser', '클렌저'),
        ('pad', '패드'),
        ('mask', '마스크/팩'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    brand = models.CharField(max_length=100)
    name = models.CharField(max_length=100)
    price = models.IntegerField()
    # URLField 기본 max_length=200. 올리브영 추적 파라미터가 붙은 URL은
    # 200자를 초과하므로 넉넉히 확장 (SQLite는 미강제, PostgreSQL은 강제).
    oliveyoung_url = models.URLField(max_length=500)
    image_url = models.URLField(max_length=500)
    category = models.CharField(max_length=50)
    # 제형(복수 가능). 제품명 규칙 파싱으로 백필한다(backfill_form).
    # "크림앤세럼"=[cream, serum], "스킨로션"=[toner, lotion]처럼 한 제품이 여러 제형일 수 있어
    # ArrayField로 둔다. 미분류는 빈 배열([]). form 필터는 form__overlap(요청 제형과 교집합)으로 건다.
    form = ArrayField(
        models.CharField(max_length=20, choices=FORM_CHOICES),
        default=list,
        blank=True,
    )
    ai_summary = models.TextField(blank=True)
    average_rating = models.FloatField(null=True, blank=True)
    review_count = models.IntegerField(default=0)
    satisfaction_by_type = models.JSONField(default=dict, blank=True)
    # RAG 벡터 검색용 임베딩 (text-embedding-3-small, 1536차원).
    # 제품 원본에서 파생되는 재생성 가능 데이터라 seed에는 넣지 않고 backfill 명령으로 채운다.
    embedding = VectorField(dimensions=1536, null=True, blank=True)

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
