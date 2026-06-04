from rest_framework import serializers
from .models import SkinProfile, UserInfo

# ModelSerializer는 모델 보고 필드 자동 생성하기 때문에 직접 다 정의할 필요 없다
class SkinProfileSerializer(serializers.ModelSerializer):
    # Meta는 직접 동작 코드 X. 클래스에 대한 설정값 담는 내부 클래스
    class Meta:
        model = SkinProfile
        # fields에는 요청/응답 모두 포함되는 필드 기재 (=수정 가능한 값들)
        fields = ['skin_type', 'concerns', 'avoid_ingredients', 'updated_at']
        # read_only_fields에서는 응답엔 포함, 요청에는 무시되는 필드들.
        # 이뜻인즉슨, 클라이언트가 값을 보내도 DB에서 무시.
        read_only_fields = ['updated_at']

class UserInfoSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserInfo
        fields = ['email', 'auth_provider', 'created_at']
        # OAuth는 전부 읽기 전용으로 필드 설정해야 함 (수정 가능 영역 X)
        # 만약 이렇게 설정 안하면 PATCH /api/v1/profile로 덮어씌울 수 있음.
        read_only_fields = ['email', 'auth_provider', 'created_at']