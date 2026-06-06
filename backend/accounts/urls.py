from django.urls import path
from . import views

urlpatterns = [
    path('profile', views.ProfileView.as_view()),
    path('auth/kakao/callback/', views.KakaoCallbackView.as_view()),
]