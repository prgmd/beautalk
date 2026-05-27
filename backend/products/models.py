import uuid
from django.db import models

class Product(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    brand = models.CharField(max_length=100)
    name = models.CharField(max_length=100)
    price = models.IntegerField()
    oliveyoung_url = models.URLField()
    image_url = models.URLField()

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
