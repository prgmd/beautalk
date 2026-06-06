from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.shortcuts import get_object_or_404, redirect
from .models import SkinProfile, UserInfo
from .serializers import SkinProfileSerializer
from rest_framework.permissions import IsAuthenticated

# OAuth 용도
import os
import requests as http  # DRF의 request 파라미터와 충돌 방지
from django.contrib.auth.models import User
from rest_framework_simplejwt.tokens import RefreshToken


class ProfileView(APIView):
    # DRF가 요청 처리 전 먼저 토큰이 있는지, 유효한지 확인하도록 오버라이딩
    # 기존 APIView에 permission_classes가 기본값으로 설정되어 있기 때문
    permission_classes = [IsAuthenticated]

    def get(self, request):
        # get은 해당 데이터가 없으면 예외가 터지므로, 먼저 filter로 있는지 여부 조사
        # filter는 쿼리셋(목록) 반환이므로, first()로 첫 번째 객체 반환하게 해야함
        # get은 단일 반환. PK로 조회할 때 자주 쓴다.
        profile = SkinProfile.objects.filter(user=request.user.userinfo).first() 

        if profile:
            serializer = SkinProfileSerializer(profile)
            return Response(serializer.data) 
        return Response(status=status.HTTP_204_NO_CONTENT)
    
    def post(self, request):
        serializer = SkinProfileSerializer(data=request.data) # request.data는 입력 데이터

        if serializer.is_valid():
            serializer.save(user=request.user.userinfo) # serializer 안에 없는 user 필드를 여기서 주입해줘야 함
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    
    def patch(self, request):
        profile = get_object_or_404(SkinProfile, user=request.user.userinfo)

        # 정보값을 일부만 수정하는 patch에서 partial=True는 사실상 필수. 안 그러면 is_valid에서 필드 누락으로 처리된다
        serializer = SkinProfileSerializer(profile, data=request.data, partial=True)
        if serializer.is_valid():
            # save()는 새 객체면 create()를 호출하고, 기존 객체면 update()를 호출한다.
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class KakaoLoginView(APIView):
    def get(self, request):
        # 카카오 인증 페이지 URL 조립 후 리다이렉트
        # 브라우저가 이 URL로 이동하면 카카오 로그인 페이지가 뜸
        # 로그인 완료 시 카카오가 redirect_uri로 code를 담아 돌려보냄
        kakao_auth_url = (
            'https://kauth.kakao.com/oauth/authorize'
            f'?client_id={os.environ.get("KAKAO_CLIENT_ID")}'
            '&redirect_uri=http://localhost:8000/api/v1/auth/kakao/callback/'
            '&response_type=code'  # Authorization Code 방식
        )
        return redirect(kakao_auth_url)


class GoogleLoginView(APIView):
    def get(self, request):
        # 구글 인증 페이지 URL 조립 후 리다이렉트
        # scope: 요청할 권한 범위 (openid + 이메일 + 프로필)
        google_auth_url = (
            'https://accounts.google.com/o/oauth2/v2/auth'
            f'?client_id={os.environ.get("GOOGLE_CLIENT_ID")}'
            '&redirect_uri=http://localhost:8000/api/v1/auth/google/callback/'
            '&response_type=code'
            '&scope=openid email profile'
        )
        return redirect(google_auth_url)

class KakaoCallbackView(APIView):
    def get(self, request):
        # 리다이렉트될 때 URL에 ?code=xxx... 형태로 들어온다.
        # request.GET에는 URL 쿼리스트링 파라미터 정보가 담겨있음.
        code = request.GET.get('code')

        # (1) 인가 코드를 통해 액세스 토큰을 교환
        token_response = http.post(
            # 카카오 토큰 발급 엔드포인트에 POST 요청을 보내고,
            'https://kauth.kakao.com/oauth/token',
            data={
                # 환경 변수에 저장해둔 REST API 키(클라이언트 ID)를 함께 보낸다.
                'grant_type': 'authorization_code',
                'client_id': os.environ.get('KAKAO_CLIENT_ID'),
                'redirect_uri': 'http://localhost:8000/api/v1/auth/kakao/callback/',
                'code': code,
            }
        )
        # 응답이 오면 JSON 형식에서 액세스 토큰만 추출
        access_token = token_response.json().get('access_token')

        # (2) 액세스 토큰으로 카카오에게 사용자 정보를 요청
        kakao_user_info = http.get(
            'https://kapi.kakao.com/v2/user/me',
            headers={'Authorization': f'Bearer {access_token}'}
        ).json()

        kakao_id = kakao_user_info.get('id')
        # 이메일 동의 안 한 사용자가 있을 경우, 없다면 kakao_id 기반의 임시 이메일 생성
        email = kakao_user_info.get('kakao_account', {}).get('email', f'{kakao_id}@kakao.com')

        # (3) Django User 조회 or 생성
        # get_or_create는 (user 객체, 생성여부 bool)로 이뤄진 튜블 반환.
        # 생성 여부는 필요 없어서 _ 처리했음. 
        django_user, _ = User.objects.get_or_create(username=f'kakao_{kakao_id}')
        user_info, _ = UserInfo.objects.get_or_create(
            email=email,
            defaults={'user': django_user, 'auth_provider': 'kakao'}
        )

        # (4) JWT 발급
        # simplejwt의 RefreshToken으로 refresh + access 토큰 쌍 생성
        refresh = RefreshToken.for_user(django_user)

        '''
        # 초기 JSON 형태 반환 구조 (테스트)
        return Response({
            'access': str(refresh.access_token),
            'refresh': str(refresh),
        })
        '''

        # 리다이렉트 링크
        return redirect(
            f'http://localhost:5173/auth/callback'
            f'?access={str(refresh.access_token)}'
            f'&refresh={str(refresh)}'
        )

class GoogleCallbackView(APIView):
    def get(self, request):
        code = request.GET.get('code')

        # (1) 인가 코드 → 액세스 토큰 교환
        # 구글은 카카오와 달리 client_secret도 필요
        token_response = http.post(
            'https://oauth2.googleapis.com/token',
            data={
                'grant_type': 'authorization_code',
                'client_id': os.environ.get('GOOGLE_CLIENT_ID'),
                'client_secret': os.environ.get('GOOGLE_CLIENT_SECRET'),
                'redirect_uri': 'http://localhost:8000/api/v1/auth/google/callback/',
                'code': code,
            }
        )
        access_token = token_response.json().get('access_token')

        # (2) 액세스 토큰 → 구글 사용자 정보 요청
        google_user_info = http.get(
            'https://www.googleapis.com/oauth2/v3/userinfo',
            headers={'Authorization': f'Bearer {access_token}'}
        ).json()

        google_id = google_user_info.get('sub')  # 구글 고유 사용자 ID
        email = google_user_info.get('email', f'{google_id}@google.com')

        # (3) Django User 조회 or 생성
        django_user, _ = User.objects.get_or_create(username=f'google_{google_id}')
        user_info, _ = UserInfo.objects.get_or_create(
            email=email,
            defaults={'user': django_user, 'auth_provider': 'google'}
        )

        # (4) JWT 발급 후 Vue로 리다이렉트
        refresh = RefreshToken.for_user(django_user)
        return redirect(
            f'http://localhost:5173/auth/callback'
            f'?access={str(refresh.access_token)}'
            f'&refresh={str(refresh)}'
        )
