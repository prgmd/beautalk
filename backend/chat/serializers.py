from rest_framework import serializers

from .models import Recommendation


class RecommendationSerializer(serializers.ModelSerializer):
    """추천 기록 1건.

    user는 요청자로 서버에서 주입하므로 입력에서 제외(read_only)한다.
    title만 클라이언트가 작성한다.
    """

    class Meta:
        model = Recommendation
        fields = ['id', 'title', 'created_at']
        read_only_fields = ['id', 'created_at']
