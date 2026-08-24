from rest_framework import generics, status
from rest_framework.permissions import IsAuthenticated, BasePermission, SAFE_METHODS
from rest_framework.response import Response
from rest_framework.views import APIView
from django.shortcuts import get_object_or_404

from .models import Post, Comment, PostLike
from .serializers import (
    PostListSerializer,
    PostDetailSerializer,
    PostWriteSerializer,
    CommentSerializer,
)


class IsAuthorOrReadOnly(BasePermission):
    """안전 메서드(GET 등)는 누구나, 변경(PATCH/DELETE)은 작성자(UserInfo)만.

    객체 단위 권한이라 generics가 get_object() 시 자동 검사한다 → 타인 글
    수정/삭제(IDOR) 차단.
    """

    def has_object_permission(self, request, view, obj):
        if request.method in SAFE_METHODS:
            return True
        author = getattr(obj, 'user', None)
        return author is not None and author == getattr(request.user, 'userinfo', None)


# ──────────────────────────────────────────────
# 게시글 — /api/v1/posts/
# ──────────────────────────────────────────────

class PostListCreateView(generics.ListCreateAPIView):
    """GET  /api/v1/posts/   — 글 목록 (?category= 필터, 페이지네이션)
    POST /api/v1/posts/   — 글 작성 (body: category/title/content/product_id?)
    """

    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        # 페이지 경계 안정성을 위해 정렬 고정. 목록 카운트(댓글·좋아요)와
        # 작성자·제품을 미리 당겨 N+1을 줄인다.
        qs = (
            Post.objects
            .select_related('user')
            .prefetch_related('products', 'comments', 'likes')
            .order_by('-created_at')
        )
        category = self.request.query_params.get('category')
        if category:
            qs = qs.filter(category=category)
        return qs

    def get_serializer_class(self):
        return PostWriteSerializer if self.request.method == 'POST' else PostListSerializer

    def create(self, request, *args, **kwargs):
        # 입력은 Write로 검증하되, 응답은 Detail 형태로 줘서 프론트가 바로 렌더하게 한다
        write = PostWriteSerializer(data=request.data)
        write.is_valid(raise_exception=True)
        post = write.save(user=request.user.userinfo)
        return Response(
            PostDetailSerializer(post, context={'request': request}).data,
            status=status.HTTP_201_CREATED,
        )


class PostDetailView(generics.RetrieveUpdateDestroyAPIView):
    """GET/PATCH/DELETE /api/v1/posts/<uuid>/ — 상세 / 수정·삭제(작성자만)."""

    queryset = (
        Post.objects
        .select_related('user')
        .prefetch_related('products', 'comments__user', 'likes')
    )
    serializer_class = PostDetailSerializer
    permission_classes = [IsAuthenticated, IsAuthorOrReadOnly]

    def update(self, request, *args, **kwargs):
        partial = kwargs.pop('partial', False)
        instance = self.get_object()  # 여기서 IsAuthorOrReadOnly 검사됨
        write = PostWriteSerializer(instance, data=request.data, partial=partial)
        write.is_valid(raise_exception=True)
        write.save()
        return Response(PostDetailSerializer(instance, context={'request': request}).data)


# ──────────────────────────────────────────────
# 댓글 — /api/v1/posts/<uuid>/comments/, /api/v1/comments/<id>/
# ──────────────────────────────────────────────

class CommentCreateView(APIView):
    """POST /api/v1/posts/<uuid>/comments/ — 댓글 작성."""

    permission_classes = [IsAuthenticated]

    def post(self, request, post_id):
        post = get_object_or_404(Post, pk=post_id)
        content = (request.data.get('content') or '').strip()
        if not content:
            return Response({'error': 'content is required'}, status=status.HTTP_400_BAD_REQUEST)

        comment = Comment.objects.create(
            post=post, user=request.user.userinfo, content=content,
        )
        return Response(
            CommentSerializer(comment, context={'request': request}).data,
            status=status.HTTP_201_CREATED,
        )


class CommentDeleteView(APIView):
    """DELETE /api/v1/comments/<id>/ — 댓글 삭제(작성자만)."""

    permission_classes = [IsAuthenticated]

    def delete(self, request, pk):
        # 본인 소유 댓글만 대상으로 삭제 → 타인 댓글 삭제(IDOR) 차단
        comment = Comment.objects.filter(pk=pk, user=request.user.userinfo).first()
        if not comment:
            return Response(status=status.HTTP_404_NOT_FOUND)

        comment.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


# ──────────────────────────────────────────────
# 좋아요 — /api/v1/posts/<uuid>/like/
# ──────────────────────────────────────────────

class PostLikeView(APIView):
    """POST/DELETE /api/v1/posts/<uuid>/like/ — 좋아요 추가/취소(토글)."""

    permission_classes = [IsAuthenticated]

    def post(self, request, post_id):
        post = get_object_or_404(Post, pk=post_id)
        # get_or_create로 같은 글을 두 번 좋아요해도 멱등하게 처리
        _, created = PostLike.objects.get_or_create(
            user=request.user.userinfo, post=post,
        )
        return Response(
            {'liked': True, 'like_count': post.likes.count()},
            status=status.HTTP_201_CREATED if created else status.HTTP_200_OK,
        )

    def delete(self, request, post_id):
        like = PostLike.objects.filter(
            user=request.user.userinfo, post_id=post_id,
        ).select_related('post').first()
        if not like:
            return Response(status=status.HTTP_404_NOT_FOUND)

        post = like.post
        like.delete()
        return Response({'liked': False, 'like_count': post.likes.count()}, status=status.HTTP_200_OK)
