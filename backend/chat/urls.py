from django.urls import path
from . import views

urlpatterns = [
    path('chat/', views.ChatView.as_view()),
    path('recommendations/', views.RecommendationListCreateView.as_view()),
]
