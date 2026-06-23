from django.urls import path
from . import views

urlpatterns = [
    path('products/', views.ProductListView.as_view()),
    path('products/<uuid:pk>/', views.ProductDetailView.as_view()),
    path('products/<uuid:pk>/posts/', views.ProductPostsView.as_view()),
    path('likes/', views.LikeListCreateView.as_view()),
    path('likes/<uuid:product_id>/', views.LikeDeleteView.as_view()),
]
