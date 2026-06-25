from django.urls import path
from . import views

urlpatterns = [
    path('chat/', views.ChatView.as_view()),
    path('recommend/', views.RecommendView.as_view()),
    path('recommendations/', views.RecommendationListView.as_view()),
    path('weather/', views.WeatherView.as_view()),
]
