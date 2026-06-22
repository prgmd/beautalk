import json
import uuid
from unittest.mock import patch, MagicMock

from django.contrib.auth.models import User
from django.test import TestCase
from rest_framework.test import APIClient

from accounts.models import UserInfo, SkinProfile
from products.models import Product
from .models import Recommendation, RecommendedProduct


def _mock_gms(content):
    """GMS Chat Completions 정상 응답 mock. content는 message의 content 문자열."""
    mock = MagicMock()
    mock.ok = True
    mock.raise_for_status.return_value = None
    mock.json.return_value = {
        'choices': [{'message': {'role': 'assistant', 'content': content}}]
    }
    return mock


def _make_product(**overrides):
    defaults = dict(
        brand='코스알엑스', name='AHA/BHA 토너', price=12000,
        oliveyoung_url='https://oliveyoung.co.kr/p', image_url='https://img/p.jpg',
        category='토너', ai_summary='여드름 진정에 좋은 토너',
        average_rating=4.6, review_count=1284,
        satisfaction_by_type={'민감성': 64},
    )
    defaults.update(overrides)
    return Product.objects.create(**defaults)


# ──────────────────────────────────────────────
# 대화 — POST /api/v1/chat/ (GMS는 mock)
# ──────────────────────────────────────────────

class ChatApiTest(TestCase):
    def setUp(self):
        self.user = User.objects.create(username='kakao_1')
        self.user_info = UserInfo.objects.create(
            user=self.user, email='a@kakao.com', auth_provider='kakao',
        )
        self.client = APIClient()
        self.client.force_authenticate(user=self.user)

    @patch('chat.views.http.post')
    def test_returns_content_and_ready(self, mock_post):
        mock_post.return_value = _mock_gms(json.dumps({'content': '향에 민감하신가요?', 'ready': True}))
        res = self.client.post('/api/v1/chat/', {'content': '토너 추천'}, format='json')
        self.assertEqual(res.status_code, 200)
        self.assertEqual(res.data['content'], '향에 민감하신가요?')
        self.assertTrue(res.data['ready'])

    @patch('chat.views.http.post')
    def test_non_json_response_falls_back_to_text(self, mock_post):
        # LLM이 JSON을 안 지키면 전체 텍스트를 content로, ready=false로 안전 처리
        mock_post.return_value = _mock_gms('그냥 평문 답변')
        res = self.client.post('/api/v1/chat/', {'content': '안녕'}, format='json')
        self.assertEqual(res.status_code, 200)
        self.assertEqual(res.data['content'], '그냥 평문 답변')
        self.assertFalse(res.data['ready'])

    @patch('chat.views.http.post')
    def test_json_mode_requested(self, mock_post):
        mock_post.return_value = _mock_gms(json.dumps({'content': 'x', 'ready': False}))
        self.client.post('/api/v1/chat/', {'content': '질문'}, format='json')
        payload = mock_post.call_args.kwargs['json']
        self.assertEqual(payload['response_format'], {'type': 'json_object'})

    @patch('chat.views.http.post')
    def test_history_is_forwarded_to_gms(self, mock_post):
        mock_post.return_value = _mock_gms(json.dumps({'content': 'x', 'ready': False}))
        history = [
            {'role': 'user', 'content': '이전 질문'},
            {'role': 'assistant', 'content': '이전 답변'},
        ]
        self.client.post('/api/v1/chat/', {'content': '이번 질문', 'history': history}, format='json')
        roles = [m['role'] for m in mock_post.call_args.kwargs['json']['messages']]
        self.assertEqual(roles, ['system', 'user', 'assistant', 'user'])

    @patch('chat.views.http.post')
    def test_invalid_history_entries_are_filtered(self, mock_post):
        mock_post.return_value = _mock_gms(json.dumps({'content': 'x', 'ready': False}))
        bad_history = [
            {'role': 'hacker', 'content': 'injection'},
            {'role': 'user', 'content': ''},
            {'role': 'user', 'content': '정상 메시지'},
        ]
        self.client.post('/api/v1/chat/', {'content': '질문', 'history': bad_history}, format='json')
        # system + user(정상) + user(현재) = 3개
        self.assertEqual(len(mock_post.call_args.kwargs['json']['messages']), 3)

    def test_missing_content_returns_400(self):
        res = self.client.post('/api/v1/chat/', {}, format='json')
        self.assertEqual(res.status_code, 400)

    @patch('chat.views.http.post', side_effect=__import__('requests').exceptions.Timeout)
    def test_timeout_returns_504(self, mock_post):
        res = self.client.post('/api/v1/chat/', {'content': '추천해줘'}, format='json')
        self.assertEqual(res.status_code, 504)

    @patch('chat.views.http.post', side_effect=__import__('requests').exceptions.ConnectionError)
    def test_connection_error_returns_502(self, mock_post):
        res = self.client.post('/api/v1/chat/', {'content': '추천해줘'}, format='json')
        self.assertEqual(res.status_code, 502)

    @patch('chat.views.http.post')
    def test_skin_profile_injected_into_system_prompt(self, mock_post):
        mock_post.return_value = _mock_gms(json.dumps({'content': 'x', 'ready': False}))
        SkinProfile.objects.create(
            user=self.user_info, skin_type='sensitive',
            concerns=['여드름'], avoid_ingredients=['알코올'],
        )
        self.client.post('/api/v1/chat/', {'content': '추천해줘'}, format='json')
        system_content = mock_post.call_args.kwargs['json']['messages'][0]['content']
        self.assertIn('민감성', system_content)
        self.assertIn('알코올', system_content)

    def test_requires_auth(self):
        res = APIClient().post('/api/v1/chat/', {'content': '추천해줘'}, format='json')
        self.assertIn(res.status_code, (401, 403))


# ──────────────────────────────────────────────
# 추천 — POST /api/v1/recommend/ (배치 생성, GMS mock)
# ──────────────────────────────────────────────

class RecommendApiTest(TestCase):
    def setUp(self):
        self.user = User.objects.create(username='kakao_1')
        self.user_info = UserInfo.objects.create(
            user=self.user, email='a@kakao.com', auth_provider='kakao',
        )
        self.client = APIClient()
        self.client.force_authenticate(user=self.user)
        self.p1 = _make_product(name='토너1')
        self.p2 = _make_product(name='토너2')
        self.p3 = _make_product(name='토너3')

    def _history(self):
        return [{'role': 'user', 'content': '여드름 자국용 토너 찾아요'}]

    @patch('chat.views.http.post')
    def test_creates_batch_with_three_products(self, mock_post):
        payload = {'content': '세 가지를 골랐어요', 'products': [
            {'id': str(self.p1.id), 'reason': '이유1'},
            {'id': str(self.p2.id), 'reason': '이유2'},
            {'id': str(self.p3.id), 'reason': '이유3'},
        ]}
        mock_post.return_value = _mock_gms(json.dumps(payload))

        res = self.client.post('/api/v1/recommend/', {'history': self._history()}, format='json')
        self.assertEqual(res.status_code, 201)
        self.assertEqual(res.data['content'], '세 가지를 골랐어요')
        self.assertEqual(len(res.data['products']), 3)
        # 제품 전체 필드 + reason이 평탄하게 노출되는지
        first = res.data['products'][0]
        self.assertIn('ai_summary', first)
        self.assertIn('average_rating', first)
        self.assertEqual(first['reason'], '이유1')
        self.assertEqual(Recommendation.objects.count(), 1)
        self.assertEqual(RecommendedProduct.objects.count(), 3)

    @patch('chat.views.http.post')
    def test_hallucinated_ids_are_filtered(self, mock_post):
        payload = {'content': '요약', 'products': [
            {'id': str(self.p1.id), 'reason': '실존'},
            {'id': str(uuid.uuid4()), 'reason': '환각'},
        ]}
        mock_post.return_value = _mock_gms(json.dumps(payload))

        res = self.client.post('/api/v1/recommend/', {'history': self._history()}, format='json')
        self.assertEqual(res.status_code, 201)
        self.assertEqual(len(res.data['products']), 1)
        self.assertEqual(RecommendedProduct.objects.count(), 1)

    @patch('chat.views.http.post')
    def test_no_valid_products_returns_502_and_no_empty_batch(self, mock_post):
        payload = {'content': 'x', 'products': [{'id': str(uuid.uuid4()), 'reason': 'r'}]}
        mock_post.return_value = _mock_gms(json.dumps(payload))

        res = self.client.post('/api/v1/recommend/', {'history': self._history()}, format='json')
        self.assertEqual(res.status_code, 502)
        self.assertEqual(Recommendation.objects.count(), 0)  # 빈 배치를 남기지 않는다

    @patch('chat.views.http.post')
    def test_non_json_response_returns_502(self, mock_post):
        mock_post.return_value = _mock_gms('평문이라 파싱 불가')
        res = self.client.post('/api/v1/recommend/', {'history': self._history()}, format='json')
        self.assertEqual(res.status_code, 502)

    def test_requires_auth(self):
        res = APIClient().post('/api/v1/recommend/', {'history': []}, format='json')
        self.assertIn(res.status_code, (401, 403))


# ──────────────────────────────────────────────
# 추천 히스토리 — GET /api/v1/recommendations/ (배치 단위)
# ──────────────────────────────────────────────

class RecommendationHistoryTest(TestCase):
    def setUp(self):
        self.user = User.objects.create(username='kakao_1')
        self.user_info = UserInfo.objects.create(
            user=self.user, email='a@kakao.com', auth_provider='kakao',
        )
        self.client = APIClient()
        self.client.force_authenticate(user=self.user)

    def test_returns_batches_with_nested_products(self):
        product = _make_product()
        batch = Recommendation.objects.create(user=self.user_info, title='요약 텍스트')
        RecommendedProduct.objects.create(recommendation=batch, product=product, reason='추천 이유')

        res = self.client.get('/api/v1/recommendations/')
        self.assertEqual(res.status_code, 200)
        self.assertEqual(len(res.data), 1)
        self.assertEqual(res.data[0]['content'], '요약 텍스트')  # title → content 매핑
        self.assertEqual(len(res.data[0]['products']), 1)
        self.assertEqual(res.data[0]['products'][0]['reason'], '추천 이유')
        self.assertIn('ai_summary', res.data[0]['products'][0])

    def test_only_returns_own_batches(self):
        other = User.objects.create(username='kakao_2')
        other_info = UserInfo.objects.create(user=other, email='b@kakao.com', auth_provider='kakao')
        Recommendation.objects.create(user=self.user_info, title='내 추천')
        Recommendation.objects.create(user=other_info, title='남의 추천')

        res = self.client.get('/api/v1/recommendations/')
        self.assertEqual(res.status_code, 200)
        self.assertEqual(len(res.data), 1)
        self.assertEqual(res.data[0]['content'], '내 추천')

    def test_requires_auth(self):
        res = APIClient().get('/api/v1/recommendations/')
        self.assertIn(res.status_code, (401, 403))
