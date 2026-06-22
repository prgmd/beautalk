from rest_framework import serializers
from .models import SkinProfile, UserInfo


class SkinProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = SkinProfile
        fields = ['skin_type', 'concerns', 'avoid_ingredients', 'updated_at']
        read_only_fields = ['updated_at']

    def validate_concerns(self, value):
        if not isinstance(value, list):
            raise serializers.ValidationError('리스트 형식이어야 합니다.')
        if any(not isinstance(item, str) or len(item) > 50 for item in value):
            raise serializers.ValidationError('각 항목은 50자 이하의 문자열이어야 합니다.')
        return value

    def validate_avoid_ingredients(self, value):
        if not isinstance(value, list):
            raise serializers.ValidationError('리스트 형식이어야 합니다.')
        if any(not isinstance(item, str) or len(item) > 50 for item in value):
            raise serializers.ValidationError('각 항목은 50자 이하의 문자열이어야 합니다.')
        return value


class UserInfoSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserInfo
        fields = ['email', 'auth_provider', 'created_at']
        read_only_fields = ['email', 'auth_provider', 'created_at']
