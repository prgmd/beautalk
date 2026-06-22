from django.contrib.auth.models import User
from django.test import TestCase
from rest_framework.test import APIClient

from accounts.models import UserInfo
from .models import Recommendation


class RecommendationApiTest(TestCase):
    """추천 기록 생성/조회 + 사용자별 격리 검증"""

    def setUp(self):
        self.user = User.objects.create(username='kakao_1')
        self.user_info = UserInfo.objects.create(
            user=self.user, email='a@kakao.com', auth_provider='kakao',
        )
        self.client = APIClient()
        self.client.force_authenticate(user=self.user)

    def test_create_recommendation(self):
        res = self.client.post('/api/v1/recommendations/', {'title': '민감성 피부 추천'}, format='json')
        self.assertEqual(res.status_code, 201)
        self.assertEqual(Recommendation.objects.filter(user=self.user_info).count(), 1)

    def test_list_only_returns_own_records(self):
        other = User.objects.create(username='kakao_2')
        other_info = UserInfo.objects.create(user=other, email='b@kakao.com', auth_provider='kakao')
        Recommendation.objects.create(user=self.user_info, title='내 추천')
        Recommendation.objects.create(user=other_info, title='남의 추천')

        res = self.client.get('/api/v1/recommendations/')
        self.assertEqual(res.status_code, 200)
        self.assertEqual(len(res.data), 1)
        self.assertEqual(res.data[0]['title'], '내 추천')

    def test_requires_auth(self):
        anon = APIClient()
        res = anon.get('/api/v1/recommendations/')
        self.assertIn(res.status_code, (401, 403))
