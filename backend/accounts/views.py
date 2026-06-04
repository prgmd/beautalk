from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.shortcuts import get_object_or_404
from .models import SkinProfile
from .serializers import SkinProfileSerializer

class ProfileView(APIView):
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
