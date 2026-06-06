from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.shortcuts import get_object_or_404
from .models import SkinProfile
from .serializers import SkinProfileSerializer
from rest_framework.permissions import IsAuthenticated

# OAuth 용도
import os
import requests as kakao_requests # DRF의 request와 충돌 방지
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
        profile = SkinProfile.objects.filter(user=request.user).first() 

        if profile:
            serializer = SkinProfileSerializer(profile)
            return Response(serializer.data) 
        return Response(None, status=status.HTTP_200_OK)
    
    def post(self, request):
        serializer = SkinProfileSerializer(data=request.data) # request.data는 입력 데이터

        if serializer.is_valid():
            serializer.save(user=request.user) # serializer 안에 없는 user 필드를 여기서 주입해줘야 함
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    
    def patch(self, request):
        profile = get_object_or_404(SkinProfile, user=request.user)

        # 정보값을 일부만 수정하는 patch에서 partial=True는 사실상 필수. 안 그러면 is_valid에서 필드 누락으로 처리된다
        serializer = SkinProfileSerializer(profile, data=request.data, partial=True)
        if serializer.is_valid():
            # save()는 새 객체면 create()를 호출하고, 기존 객체면 update()를 호출한다.
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class KakaoCallbackView(APIView):
    def get(self, request):
        # 리다이렉트될 때 URL에 ?code=xxx... 형태로 들어온다.
        # request.GET에는 URL 쿼리스트링 파라미터 정보가 담겨있음.
        code = request.GET.get('code')

        # (1) 인가 코드를 통해 액세스 토큰을 교환
        token_response = kakao_requests.post(
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
        user_info = kakao_requests.get(
            'https://kapi.kakao.com/v2/user/me',
            headers={'Authorization': f'Bearer {access_token}'}
        ).json()

        kakao_id = user_info.get('id')
        # 이메일 동의 안 한 사용자가 있을 경우, 없다면 kakao_id 기반의 임시 이메일 생성
        email = user_info.get('kakao_account', {}).get('email', f'{kakao_id}@kakao.com')

        # (3) Django User 조회 or 생성
        # get_or_create는 (user 객체, 생성여부 bool)로 이뤄진 튜블 반환.
        # 생성 여부는 필요 없어서 _ 처리했음. 
        user, _ = User.objects.get_or_create(
            username=f'kakao_{kakao_id}',
            defaults={'email': email} # 최초 생성시에만 적용되는 필드
        )

        # (4) JWT 발급
        # simplejwt의 RefreshToken으로 refresh + access 토큰 쌍 생성
        refresh = RefreshToken.for_user(user)
        return Response({
            'access': str(refresh.access_token),
            'refresh': str(refresh),
        })
