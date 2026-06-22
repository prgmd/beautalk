from django.contrib.auth.models import User
from django.test import TestCase
from rest_framework.test import APIClient
from rest_framework_simplejwt.tokens import RefreshToken

from .models import UserInfo, SkinProfile
from .views import resolve_oauth_user, REFRESH_COOKIE_NAME


class LogoutBlacklistTest(TestCase):
    """로그아웃 시 refresh 토큰이 실제로 블랙리스트되는지 (프론트팀 지적 #1)"""

    def setUp(self):
        self.user = User.objects.create(username='kakao_1')
        UserInfo.objects.create(user=self.user, email='a@kakao.com', auth_provider='kakao')

    def test_logout_blacklists_refresh_token(self):
        refresh = str(RefreshToken.for_user(self.user))

        # 로그아웃 (쿠키에 refresh 토큰 동봉 — path가 넓어졌으므로 전송됨)
        client = APIClient()
        client.force_authenticate(user=self.user)
        client.cookies[REFRESH_COOKIE_NAME] = refresh
        res = client.post('/api/v1/auth/logout/')
        self.assertEqual(res.status_code, 204)

        # 로그아웃된 refresh 토큰으로 갱신 시도 → 블랙리스트되어 401이어야 함
        client2 = APIClient()
        client2.cookies[REFRESH_COOKIE_NAME] = refresh
        res2 = client2.post('/api/v1/auth/token/refresh')
        self.assertEqual(res2.status_code, 401)


class AccountDeleteTest(TestCase):
    """회원 탈퇴 시 계정 + 연관 데이터가 삭제되고 토큰이 무효화되는지"""

    def setUp(self):
        self.user = User.objects.create(username='kakao_1')
        UserInfo.objects.create(user=self.user, email='a@kakao.com', auth_provider='kakao')

    def test_delete_removes_user_and_blacklists_token(self):
        refresh = str(RefreshToken.for_user(self.user))

        client = APIClient()
        client.force_authenticate(user=self.user)
        client.cookies[REFRESH_COOKIE_NAME] = refresh
        res = client.delete('/api/v1/account/')
        self.assertEqual(res.status_code, 204)

        # 계정과 UserInfo가 CASCADE로 함께 사라져야 함
        self.assertFalse(User.objects.filter(username='kakao_1').exists())
        self.assertEqual(UserInfo.objects.count(), 0)

        # 탈퇴 시 블랙리스트된 refresh 토큰으로는 갱신 불가
        client2 = APIClient()
        client2.cookies[REFRESH_COOKIE_NAME] = refresh
        res2 = client2.post('/api/v1/auth/token/refresh')
        self.assertEqual(res2.status_code, 401)


class EmailDuplicateTest(TestCase):
    """동일 이메일을 가진 타 provider 가입 시 차단되는지 (프론트팀 지적 #2)"""

    def test_existing_email_blocks_new_provider(self):
        google_user = User.objects.create(username='google_1')
        UserInfo.objects.create(user=google_user, email='dup@x.com', auth_provider='google')

        # 같은 이메일로 신규 카카오 가입 시도 → None 반환 (호출 측에서 email_duplicated 처리)
        result = resolve_oauth_user('kakao_99', 'dup@x.com', 'kakao')
        self.assertIsNone(result)
        # 빈 User 레코드가 남지 않아야 함
        self.assertFalse(User.objects.filter(username='kakao_99').exists())

    def test_returning_user_reuses_account(self):
        user = User.objects.create(username='kakao_1')
        UserInfo.objects.create(user=user, email='a@kakao.com', auth_provider='kakao')

        # 동일 카카오 사용자 재로그인 → 같은 user 반환, 중복 UserInfo 생성 없음
        result = resolve_oauth_user('kakao_1', 'a@kakao.com', 'kakao')
        self.assertEqual(result, user)
        self.assertEqual(UserInfo.objects.count(), 1)


class TokenExchangeTest(TestCase):
    """세션 임시 토큰 → access(바디) + refresh(HttpOnly 쿠키) 교환"""

    def test_exchange_returns_access_and_sets_httponly_cookie(self):
        user = User.objects.create(username='kakao_1')
        UserInfo.objects.create(user=user, email='a@kakao.com', auth_provider='kakao')
        refresh = RefreshToken.for_user(user)

        client = APIClient()
        session = client.session
        session['pending_access'] = str(refresh.access_token)
        session['pending_refresh'] = str(refresh)
        session.save()

        res = client.get('/api/v1/auth/exchange/')
        self.assertEqual(res.status_code, 200)
        self.assertIn('access', res.data)

        cookie = res.cookies.get(REFRESH_COOKIE_NAME)
        self.assertIsNotNone(cookie)
        self.assertTrue(cookie['httponly'])
        self.assertEqual(cookie['path'], '/api/v1/auth')


class StateCsrfTest(TestCase):
    """state 불일치 시 OAuth 콜백이 외부 호출 없이 차단되는지"""

    def test_callback_rejects_mismatched_state(self):
        client = APIClient()
        res = client.get('/api/v1/auth/kakao/callback/?code=x&state=tampered')
        self.assertEqual(res.status_code, 302)
        self.assertIn('error=csrf_detected', res['Location'])


class SkinProfileValidationTest(TestCase):
    """JSONField 입력 검증"""

    def setUp(self):
        self.user = User.objects.create(username='kakao_1')
        UserInfo.objects.create(user=self.user, email='a@kakao.com', auth_provider='kakao')
        self.client = APIClient()
        self.client.force_authenticate(user=self.user)

    def test_rejects_non_list_concerns(self):
        res = self.client.post('/api/v1/profile', {
            'skin_type': 'dry',
            'concerns': {'not': 'a list'},
            'avoid_ingredients': [],
        }, format='json')
        self.assertEqual(res.status_code, 400)

    def test_accepts_valid_list(self):
        res = self.client.post('/api/v1/profile', {
            'skin_type': 'dry',
            'concerns': ['건조함', '각질'],
            'avoid_ingredients': ['알코올'],
        }, format='json')
        self.assertEqual(res.status_code, 201)
        self.assertTrue(SkinProfile.objects.filter(user=self.user.userinfo).exists())
