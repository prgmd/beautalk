import os
import secrets

import requests as http
from django.contrib.auth.models import User
from django.shortcuts import get_object_or_404, redirect
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.exceptions import TokenError
from rest_framework_simplejwt.tokens import RefreshToken

from .models import SkinProfile, UserInfo
from .serializers import SkinProfileSerializer


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

        # (3) Django User + UserInfo 조회/생성
        django_user, _ = User.objects.get_or_create(username=f'kakao_{kakao_id}')
        UserInfo.objects.get_or_create(
            auth_provider='kakao',
            email=email,
            defaults={'user': django_user},
        )

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

        # (3) Django User + UserInfo 조회/생성
        django_user, _ = User.objects.get_or_create(username=f'google_{google_id}')
        UserInfo.objects.get_or_create(
            auth_provider='google',
            email=email,
            defaults={'user': django_user},
        )

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
        response.set_cookie(
            'bt_refresh',
            refresh,
            httponly=True,
            samesite='Lax',
            path='/api/v1/auth/token/refresh',
            max_age=7 * 24 * 60 * 60,
        )
        return response


# ──────────────────────────────────────────────
# 토큰 갱신 (HttpOnly 쿠키 → 새 access 토큰)
# ──────────────────────────────────────────────

class CookieTokenRefreshView(APIView):
    def post(self, request):
        refresh_token = request.COOKIES.get('bt_refresh')
        if not refresh_token:
            return Response({'error': 'refresh token not found'}, status=status.HTTP_401_UNAUTHORIZED)

        try:
            refresh = RefreshToken(refresh_token)
            access = str(refresh.access_token)
        except TokenError:
            return Response({'error': 'invalid or expired refresh token'}, status=status.HTTP_401_UNAUTHORIZED)

        response = Response({'access': access})
        # ROTATE_REFRESH_TOKENS=True이면 새 refresh 토큰이 발급되므로 쿠키 갱신
        response.set_cookie(
            'bt_refresh',
            str(refresh),
            httponly=True,
            samesite='Lax',
            path='/api/v1/auth/token/refresh',
            max_age=7 * 24 * 60 * 60,
        )
        return response


# ──────────────────────────────────────────────
# 로그아웃 (refresh 토큰 블랙리스트 + 쿠키 삭제)
# ──────────────────────────────────────────────

class LogoutView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        refresh_token = request.COOKIES.get('bt_refresh')
        if refresh_token:
            try:
                RefreshToken(refresh_token).blacklist()
            except TokenError:
                pass  # 이미 만료/블랙리스트된 토큰이면 무시

        response = Response(status=status.HTTP_204_NO_CONTENT)
        response.delete_cookie('bt_refresh', path='/api/v1/auth/token/refresh')
        return response
