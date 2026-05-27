import uuid
from django.db import models

class UserInfo(models.Model):
    AUTH = [('kakao', 'Kakao'), ('google', 'Google'),]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    email = models.EmailField(unique=True)
    auth_provider = models.CharField(max_length=10, choices=AUTH)
    created_at = models.DateTimeField(auto_now_add=True)
    
    # 상수는 클래스 위에 넣는 것이 관례
    # 클래스 이름을 User로 하는 것은 비추천. 기본 Django User 모델과 충돌 가능성.

class SkinProfile(models.Model):
    SKIN_TYPE = [('dry', '건성'), ('oily', '지성'), ('combination', '복합성'), ('sensitive', '민감성')]

    user = models.OneToOneField(UserInfo, on_delete=models.CASCADE)
    skin_type = models.CharField(max_length=15, choices=SKIN_TYPE)
    concerns = models.JSONField()
    avoid_ingredients = models.JSONField()
    updated_at = models.DateTimeField(auto_now=True)

    # 1:1 관계를 고려해 ForeignKey 대신 OneToOneField 사용
    # 자동으로 _id 붙여서 생성됨 (user_id로 만들어짐)