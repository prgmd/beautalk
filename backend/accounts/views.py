import os
import secrets

import requests as http
from django.conf import settings
from django.contrib.auth.models import User
from django.shortcuts import get_object_or_404, redirect
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.exceptions import TokenError
from rest_framework_simplejwt.tokens import RefreshToken

from .models import SkinProfile, UserInfo
from .serializers import SkinProfileSerializer, UserInfoSerializer


# ──────────────────────────────────────────────
# Refresh 쿠키 설정
# ──────────────────────────────────────────────

FRONTEND_LOGIN_URL = 'http://localhost:5173/login'

REFRESH_COOKIE_NAME = 'bt_refresh'
# logout(/api/v1/auth/logout/)과 refresh(/api/v1/auth/token/refresh) 요청에
# 모두 쿠키가 전송되도록 path를 /api/v1/auth로 넓힌다.
# (좁히면 logout 요청에 쿠키가 안 실려 블랙리스트가 동작하지 않는다)
REFRESH_COOKIE_PATH = '/api/v1/auth'
REFRESH_COOKIE_MAX_AGE = 7 * 24 * 60 * 60  # 7일 (REFRESH_TOKEN_LIFETIME과 일치)


def set_refresh_cookie(response, token):
    response.set_cookie(
        REFRESH_COOKIE_NAME,
        token,
        httponly=True,
        # 운영(HTTPS)에서만 쿠키를 전송하도록 Secure를 켠다. 로컬은 HTTP라 DEBUG=True일 때
        # 꺼야 쿠키가 동작하므로 DEBUG에 연동(=배포 시 자동으로 Secure 활성).
        secure=not settings.DEBUG,
        samesite='Lax',
        path=REFRESH_COOKIE_PATH,
        max_age=REFRESH_COOKIE_MAX_AGE,
    )


def resolve_oauth_user(username, email, provider):
    """
    provider_id를 인코딩한 username으로 사용자를 식별한다.
    이메일이 아니라 (provider + provider_id)로 식별하므로
    동일 이메일을 가진 타 provider 계정과 섞이지 않는다.

    신규 가입인데 해당 이메일이 다른 계정에서 이미 사용 중이면
    None을 반환해 호출 측이 email_duplicated로 처리하게 한다.
    """
    django_user, created = User.objects.get_or_create(username=username)
    user_info = UserInfo.objects.filter(user=django_user).first()

    if user_info is None:
        # 신규 가입 — 이메일 선점 여부 확인 (계정 탈취/충돌 방지)
        if UserInfo.objects.filter(email=email).exists():
            if created:
                django_user.delete()  # 가입 실패 시 빈 User 레코드 정리
            return None
        UserInfo.objects.create(user=django_user, email=email, auth_provider=provider)

    return django_user


# ──────────────────────────────────────────────
# Skin Profile
# ──────────────────────────────────────────────

class ProfileView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        profile = SkinProfile.objects.filter(user=request.user.userinfo).first()
        if profile:
            return Response(SkinProfileSerializer(profile).data)
        return Response(status=status.HTTP_204_NO_CONTENT)

    def post(self, request):
        existing = SkinProfile.objects.filter(user=request.user.userinfo).first()
        serializer = (
            SkinProfileSerializer(existing, data=request.data)
            if existing
            else SkinProfileSerializer(data=request.data)
        )
        if serializer.is_valid():
            serializer.save(user=request.user.userinfo)
            return Response(
                serializer.data,
                status=status.HTTP_200_OK if existing else status.HTTP_201_CREATED,
            )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def patch(self, request):
        profile = get_object_or_404(SkinProfile, user=request.user.userinfo)
        serializer = SkinProfileSerializer(profile, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


# ──────────────────────────────────────────────
# OAuth — 카카오
# ──────────────────────────────────────────────

class KakaoLoginView(APIView):
    def get(self, request):
        state = secrets.token_urlsafe(16)
        request.session['oauth_state'] = state

        kakao_auth_url = (
            'https://kauth.kakao.com/oauth/authorize'
            f'?client_id={os.environ.get("KAKAO_CLIENT_ID")}'
            '&redirect_uri=http://localhost:8000/api/v1/auth/kakao/callback/'
            '&response_type=code'
            f'&state={state}'
        )
        return redirect(kakao_auth_url)


class KakaoCallbackView(APIView):
    def get(self, request):
        # CSRF 검증
        returned_state = request.GET.get('state')
        session_state = request.session.pop('oauth_state', None)
        if not returned_state or returned_state != session_state:
            return redirect('http://localhost:5173/login?error=csrf_detected')

        # OAuth 에러 처리
        if request.GET.get('error'):
            return redirect('http://localhost:5173/login?error=oauth_failed')

        code = request.GET.get('code')
        if not code:
            return redirect('http://localhost:5173/login?error=missing_code')

        # (1) 인가 코드 → 카카오 액세스 토큰 교환
        token_response = http.post(
            'https://kauth.kakao.com/oauth/token',
            data={
                'grant_type': 'authorization_code',
                'client_id': os.environ.get('KAKAO_CLIENT_ID'),
                'client_secret': os.environ.get('KAKAO_CLIENT_SECRET'),
                'redirect_uri': 'http://localhost:8000/api/v1/auth/kakao/callback/',
                'code': code,
            },
            timeout=10,
        )
        if not token_response.ok:
            return redirect('http://localhost:5173/login?error=token_exchange_failed')

        kakao_access_token = token_response.json().get('access_token')
        if not kakao_access_token:
            return redirect('http://localhost:5173/login?error=token_exchange_failed')

        # (2) 카카오 액세스 토큰 → 사용자 정보
        user_info_response = http.get(
            'https://kapi.kakao.com/v2/user/me',
            headers={'Authorization': f'Bearer {kakao_access_token}'},
            timeout=10,
        )
        if not user_info_response.ok:
            return redirect('http://localhost:5173/login?error=userinfo_failed')

        kakao_user_info = user_info_response.json()
        kakao_id = kakao_user_info.get('id')
        email = kakao_user_info.get('kakao_account', {}).get('email', f'{kakao_id}@kakao.com')

        # (3) provider_id 기반으로 사용자 식별 (이메일 중복 시 명시적 에러)
        django_user = resolve_oauth_user(f'kakao_{kakao_id}', email, 'kakao')
        if django_user is None:
            return redirect(f'{FRONTEND_LOGIN_URL}?error=email_duplicated')

        # (4) JWT 발급 → 세션에 임시 저장
        refresh = RefreshToken.for_user(django_user)
        request.session['pending_access'] = str(refresh.access_token)
        request.session['pending_refresh'] = str(refresh)

        return redirect('http://localhost:5173/auth/callback')


# ──────────────────────────────────────────────
# OAuth — 구글
# ──────────────────────────────────────────────

class GoogleLoginView(APIView):
    def get(self, request):
        state = secrets.token_urlsafe(16)
        request.session['oauth_state'] = state

        google_auth_url = (
            'https://accounts.google.com/o/oauth2/v2/auth'
            f'?client_id={os.environ.get("GOOGLE_CLIENT_ID")}'
            '&redirect_uri=http://localhost:8000/api/v1/auth/google/callback/'
            '&response_type=code'
            '&scope=openid email profile'
            f'&state={state}'
        )
        return redirect(google_auth_url)


class GoogleCallbackView(APIView):
    def get(self, request):
        # CSRF 검증
        returned_state = request.GET.get('state')
        session_state = request.session.pop('oauth_state', None)
        if not returned_state or returned_state != session_state:
            return redirect('http://localhost:5173/login?error=csrf_detected')

        if request.GET.get('error'):
            return redirect('http://localhost:5173/login?error=oauth_failed')

        code = request.GET.get('code')
        if not code:
            return redirect('http://localhost:5173/login?error=missing_code')

        # (1) 인가 코드 → 구글 액세스 토큰 교환
        token_response = http.post(
            'https://oauth2.googleapis.com/token',
            data={
                'grant_type': 'authorization_code',
                'client_id': os.environ.get('GOOGLE_CLIENT_ID'),
                'client_secret': os.environ.get('GOOGLE_CLIENT_SECRET'),
                'redirect_uri': 'http://localhost:8000/api/v1/auth/google/callback/',
                'code': code,
            },
            timeout=10,
        )
        if not token_response.ok:
            return redirect('http://localhost:5173/login?error=token_exchange_failed')

        google_access_token = token_response.json().get('access_token')
        if not google_access_token:
            return redirect('http://localhost:5173/login?error=token_exchange_failed')

        # (2) 구글 액세스 토큰 → 사용자 정보
        user_info_response = http.get(
            'https://www.googleapis.com/oauth2/v3/userinfo',
            headers={'Authorization': f'Bearer {google_access_token}'},
            timeout=10,
        )
        if not user_info_response.ok:
            return redirect('http://localhost:5173/login?error=userinfo_failed')

        google_user_info = user_info_response.json()
        google_id = google_user_info.get('sub')
        email = google_user_info.get('email', f'{google_id}@google.com')

        # (3) provider_id 기반으로 사용자 식별 (이메일 중복 시 명시적 에러)
        django_user = resolve_oauth_user(f'google_{google_id}', email, 'google')
        if django_user is None:
            return redirect(f'{FRONTEND_LOGIN_URL}?error=email_duplicated')

        # (4) JWT 발급 → 세션에 임시 저장
        refresh = RefreshToken.for_user(django_user)
        request.session['pending_access'] = str(refresh.access_token)
        request.session['pending_refresh'] = str(refresh)

        return redirect('http://localhost:5173/auth/callback')


# ──────────────────────────────────────────────
# 토큰 교환 (세션 → HttpOnly 쿠키 + 응답 바디)
# ──────────────────────────────────────────────

class TokenExchangeView(APIView):
    """
    OAuth 콜백 직후 프론트엔드가 호출하는 일회성 엔드포인트.
    세션에 임시 저장된 JWT를 꺼내, access는 응답 바디로, refresh는 HttpOnly 쿠키로 전달.
    """
    def get(self, request):
        access = request.session.pop('pending_access', None)
        refresh = request.session.pop('pending_refresh', None)

        if not access or not refresh:
            return Response({'error': 'no pending token'}, status=status.HTTP_401_UNAUTHORIZED)

        response = Response({'access': access})
        set_refresh_cookie(response, refresh)
        return response


# ──────────────────────────────────────────────
# 토큰 갱신 (HttpOnly 쿠키 → 새 access 토큰)
# ──────────────────────────────────────────────

class CookieTokenRefreshView(APIView):
    def post(self, request):
        refresh_token = request.COOKIES.get(REFRESH_COOKIE_NAME)
        if not refresh_token:
            return Response({'error': 'refresh token not found'}, status=status.HTTP_401_UNAUTHORIZED)

        try:
            refresh = RefreshToken(refresh_token)
            # 토큰 서명/만료/블랙리스트 검증을 통과해도, 그 사이 계정이 탈퇴(삭제)
            # 또는 비활성화됐을 수 있다. 회원 탈퇴 시 simplejwt 블랙리스트 레코드는
            # User와 함께 CASCADE 삭제되므로, 사용자 존재 여부를 직접 확인해야
            # 탈퇴 후 토큰으로 access를 재발급받는 구멍을 막을 수 있다.
            user_id = refresh.payload.get('user_id')
            if not User.objects.filter(pk=user_id, is_active=True).exists():
                raise TokenError('user no longer exists')
            access = str(refresh.access_token)
        except TokenError:
            return Response({'error': 'invalid or expired refresh token'}, status=status.HTTP_401_UNAUTHORIZED)

        response = Response({'access': access})
        # 동일 refresh 토큰 유효기간 동안 쿠키 만료시간을 갱신해 슬라이딩 세션처럼 동작시킨다
        set_refresh_cookie(response, str(refresh))
        return response


# ──────────────────────────────────────────────
# 로그아웃 (refresh 토큰 블랙리스트 + 쿠키 삭제)
# ──────────────────────────────────────────────

class LogoutView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        refresh_token = request.COOKIES.get(REFRESH_COOKIE_NAME)
        if refresh_token:
            try:
                RefreshToken(refresh_token).blacklist()
            except TokenError:
                pass  # 이미 만료/블랙리스트된 토큰이면 무시

        response = Response(status=status.HTTP_204_NO_CONTENT)
        response.delete_cookie(REFRESH_COOKIE_NAME, path=REFRESH_COOKIE_PATH)
        return response


# ──────────────────────────────────────────────
# 계정 (조회 + 회원 탈퇴)
# ──────────────────────────────────────────────

class AccountView(APIView):
    """GET    /api/v1/account/  — 내 계정 정보 (이메일, 가입 경로, 닉네임, 가입일)
    PATCH  /api/v1/account/  — 계정 정보 수정 (닉네임)
    DELETE /api/v1/account/  — 회원 탈퇴

    탈퇴는 되돌릴 수 없는 작업이므로 다음 순서를 지킨다:
      1) 남아있는 refresh 토큰을 블랙리스트해 탈퇴 후 토큰 재사용을 막는다.
      2) Django User를 삭제한다 → FK on_delete=CASCADE 연쇄로
         UserInfo · SkinProfile · Like · InUseProduct · Recommendation 까지 함께 삭제된다.
      3) refresh 쿠키를 제거해 클라이언트 상태도 깨끗하게 정리한다.
    """

    permission_classes = [IsAuthenticated]

    def get(self, request):
        return Response(UserInfoSerializer(request.user.userinfo).data)

    def patch(self, request):
        # 닉네임 등 편집 가능한 계정 정보 수정 (email/provider는 read_only라 무시됨)
        serializer = UserInfoSerializer(
            request.user.userinfo, data=request.data, partial=True,
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)

    def delete(self, request):
        refresh_token = request.COOKIES.get(REFRESH_COOKIE_NAME)
        if refresh_token:
            try:
                RefreshToken(refresh_token).blacklist()
            except TokenError:
                pass  # 이미 만료/블랙리스트된 토큰이면 무시

        # Django User 삭제 → OneToOne/ForeignKey CASCADE로 관련 데이터 일괄 삭제
        request.user.delete()

        response = Response(status=status.HTTP_204_NO_CONTENT)
        response.delete_cookie(REFRESH_COOKIE_NAME, path=REFRESH_COOKIE_PATH)
        return response
