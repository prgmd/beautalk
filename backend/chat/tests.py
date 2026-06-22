from unittest.mock import patch, MagicMock

from django.contrib.auth.models import User
from django.test import TestCase
from rest_framework.test import APIClient

from accounts.models import UserInfo, SkinProfile
from products.models import Product
from .models import Recommendation


# ──────────────────────────────────────────────
# 추천 기록 API
# ──────────────────────────────────────────────

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


# ──────────────────────────────────────────────
# 챗봇 API (GMS HTTP 호출은 mock으로 대체)
# ──────────────────────────────────────────────

def _mock_gms_response(content='테스트 AI 응답입니다.'):
    """GMS API 정상 응답을 흉내 내는 mock 객체를 반환한다."""
    mock = MagicMock()
    mock.ok = True
    mock.json.return_value = {
        'choices': [{'message': {'role': 'assistant', 'content': content}}]
    }
    return mock


class ChatApiTest(TestCase):
    def setUp(self):
        self.user = User.objects.create(username='kakao_1')
        self.user_info = UserInfo.objects.create(
            user=self.user, email='a@kakao.com', auth_provider='kakao',
        )
        self.client = APIClient()
        self.client.force_authenticate(user=self.user)

    @patch('chat.views.http.post', return_value=_mock_gms_response())
    def test_returns_ai_content(self, mock_post):
        res = self.client.post('/api/v1/chat/', {'content': '추천해줘'}, format='json')
        self.assertEqual(res.status_code, 200)
        self.assertIn('content', res.data)
        self.assertEqual(res.data['content'], '테스트 AI 응답입니다.')

    @patch('chat.views.http.post', return_value=_mock_gms_response())
    def test_history_is_forwarded_to_gms(self, mock_post):
        history = [
            {'role': 'user', 'content': '이전 질문'},
            {'role': 'assistant', 'content': '이전 답변'},
        ]
        self.client.post('/api/v1/chat/', {'content': '이번 질문', 'history': history}, format='json')

        call_messages = mock_post.call_args.kwargs['json']['messages']
        roles = [m['role'] for m in call_messages]
        # system → user(이전) → assistant(이전) → user(현재) 순서여야 한다
        self.assertEqual(roles, ['system', 'user', 'assistant', 'user'])

    @patch('chat.views.http.post', return_value=_mock_gms_response())
    def test_invalid_history_entries_are_filtered(self, mock_post):
        # role이 잘못됐거나 content가 없는 항목은 필터링돼야 한다
        bad_history = [
            {'role': 'hacker', 'content': 'injection'},
            {'role': 'user', 'content': ''},
            {'role': 'user', 'content': '정상 메시지'},
        ]
        self.client.post('/api/v1/chat/', {'content': '질문', 'history': bad_history}, format='json')

        call_messages = mock_post.call_args.kwargs['json']['messages']
        # system + user(정상) + user(현재) = 3개
        self.assertEqual(len(call_messages), 3)

    def test_missing_content_returns_400(self):
        res = self.client.post('/api/v1/chat/', {}, format='json')
        self.assertEqual(res.status_code, 400)

    @patch('chat.views.http.post', side_effect=__import__('requests').exceptions.Timeout)
    def test_gms_timeout_returns_504(self, mock_post):
        res = self.client.post('/api/v1/chat/', {'content': '추천해줘'}, format='json')
        self.assertEqual(res.status_code, 504)

    @patch('chat.views.http.post', side_effect=__import__('requests').exceptions.ConnectionError)
    def test_gms_connection_error_returns_502(self, mock_post):
        res = self.client.post('/api/v1/chat/', {'content': '추천해줘'}, format='json')
        self.assertEqual(res.status_code, 502)

    @patch('chat.views.http.post', return_value=_mock_gms_response())
    def test_skin_profile_injected_into_system_prompt(self, mock_post):
        # SkinProfile이 있을 때 시스템 프롬프트에 피부 정보가 포함되는지
        SkinProfile.objects.create(
            user=self.user_info,
            skin_type='sensitive',
            concerns=['여드름'],
            avoid_ingredients=['알코올'],
        )
        self.client.post('/api/v1/chat/', {'content': '추천해줘'}, format='json')

        system_content = mock_post.call_args.kwargs['json']['messages'][0]['content']
        self.assertIn('민감성', system_content)
        self.assertIn('알코올', system_content)

    def test_requires_auth(self):
        anon = APIClient()
        res = anon.post('/api/v1/chat/', {'content': '추천해줘'}, format='json')
        self.assertIn(res.status_code, (401, 403))
