from django.urls import path
from . import views

urlpatterns = [
    path('profile', views.ProfileView.as_view()),
    path('auth/kakao/callback/', views.KakaoCallbackView.as_view()),
    path('auth/google/callback/', views.GoogleCallbackView.as_view()),
    path('auth/kakao/login/', views.KakaoLoginView.as_view()),
    path('auth/google/login/', views.GoogleLoginView.as_view()),
]