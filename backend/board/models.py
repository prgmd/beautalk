import uuid
from django.db import models


class Post(models.Model):
    """게시판 글.

    용도별 카테고리(자유/Q&A·팁/세일)로 나뉘고, 제품을 선택적으로 태그해
    추천 서비스와 연결한다(게시글 → 제품 정참조). id를 UUID로 둬서 URL에서
    글 수를 추측하는 enumeration을 막는다(제품·UserInfo와도 톤 일치).
    """

    CATEGORY_CHOICES = [
        ('free', '자유'),
        ('qna', 'Q&A·팁'),
        ('sale', '세일 정보'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(
        'accounts.UserInfo', on_delete=models.CASCADE, related_name='posts',
    )
    category = models.CharField(max_length=20, choices=CATEGORY_CHOICES, default='free')
    title = models.CharField(max_length=200)
    content = models.TextField()
    # 제품 태그(선택). 제품이 삭제돼도 글은 남도록 SET_NULL.
    # related_name='tagged_posts'로 '제품 → 그 제품이 태그된 글' 역참조를 연다.
    product = models.ForeignKey(
        'products.Product', null=True, blank=True,
        on_delete=models.SET_NULL, related_name='tagged_posts',
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']


class Comment(models.Model):
    post = models.ForeignKey(Post, on_delete=models.CASCADE, related_name='comments')
    user = models.ForeignKey('accounts.UserInfo', on_delete=models.CASCADE)
    content = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['created_at']


class PostLike(models.Model):
    """게시글 좋아요. 기존 products.Like 패턴 그대로(유저-대상 unique)."""

    user = models.ForeignKey('accounts.UserInfo', on_delete=models.CASCADE)
    post = models.ForeignKey(Post, on_delete=models.CASCADE, related_name='likes')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=['user', 'post'], name='unique_post_like'),
        ]
