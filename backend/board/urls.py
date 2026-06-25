from django.urls import path
from . import views

urlpatterns = [
    path('posts/', views.PostListCreateView.as_view()),
    path('posts/<uuid:pk>/', views.PostDetailView.as_view()),
    path('posts/<uuid:post_id>/comments/', views.CommentCreateView.as_view()),
    path('posts/<uuid:post_id>/like/', views.PostLikeView.as_view()),
    path('comments/<int:pk>/', views.CommentDeleteView.as_view()),
]
