from rest_framework import serializers

from products.models import Product
from products.serializers import ProductSerializer
from .models import Post, Comment


def _author_name(user_info) -> str:
    """작성자 표시명. 닉네임이 있으면 닉네임, 없으면 이메일 로컬파트만 노출한다
    (전체 이메일 노출은 개인정보라 피한다). UserInfo가 없으면 '익명'.
    """
    if user_info:
        if user_info.nickname:
            return user_info.nickname
        if user_info.email:
            return user_info.email.split('@')[0]
    return '익명'


class CommentSerializer(serializers.ModelSerializer):
    author = serializers.SerializerMethodField()

    class Meta:
        model = Comment
        fields = ['id', 'author', 'content', 'created_at']
        read_only_fields = ['id', 'author', 'created_at']

    def get_author(self, obj):
        return _author_name(obj.user)


class PostListSerializer(serializers.ModelSerializer):
    """목록용 — 본문은 빼고 카운트·메타만 가볍게 내린다."""

    author = serializers.SerializerMethodField()
    category_label = serializers.CharField(source='get_category_display', read_only=True)
    comment_count = serializers.IntegerField(source='comments.count', read_only=True)
    like_count = serializers.IntegerField(source='likes.count', read_only=True)
    has_product = serializers.SerializerMethodField()

    class Meta:
        model = Post
        fields = [
            'id', 'category', 'category_label', 'title', 'author',
            'comment_count', 'like_count', 'has_product', 'created_at',
        ]

    def get_author(self, obj):
        return _author_name(obj.user)

    def get_has_product(self, obj):
        return obj.products.exists()


class PostDetailSerializer(serializers.ModelSerializer):
    """상세 — 본문 + 댓글 중첩 + 태그된 제품 카드(ProductSerializer 재사용)."""

    author = serializers.SerializerMethodField()
    category_label = serializers.CharField(source='get_category_display', read_only=True)
    comments = CommentSerializer(many=True, read_only=True)
    products = ProductSerializer(many=True, read_only=True)
    like_count = serializers.IntegerField(source='likes.count', read_only=True)

    class Meta:
        model = Post
        fields = [
            'id', 'category', 'category_label', 'title', 'content', 'author',
            'products', 'comments', 'like_count', 'created_at', 'updated_at',
        ]
        read_only_fields = ['id', 'author', 'created_at', 'updated_at']

    def get_author(self, obj):
        return _author_name(obj.user)


class PostWriteSerializer(serializers.ModelSerializer):
    """작성/수정 입력용. 제품 태그는 product_ids(UUID 배열)로 받는다(복수·선택).

    user는 view에서 save(user=...)로 강제 주입하므로 입력으로 받지 않는다
    (클라이언트가 user를 지정하면 타인 명의 글을 쓰는 IDOR이 된다).
    """

    product_ids = serializers.ListField(
        child=serializers.UUIDField(), write_only=True, required=False,
    )

    class Meta:
        model = Post
        fields = ['id', 'category', 'title', 'content', 'product_ids']
        read_only_fields = ['id']

    def validate_product_ids(self, value):
        if value:
            existing = set(
                Product.objects.filter(pk__in=value).values_list('id', flat=True)
            )
            missing = [str(v) for v in value if v not in existing]
            if missing:
                raise serializers.ValidationError(f'존재하지 않는 제품: {missing}')
        return value

    def create(self, validated_data):
        # M2M은 인스턴스 저장 후에야 set 가능
        product_ids = validated_data.pop('product_ids', None)
        post = Post.objects.create(**validated_data)
        if product_ids:
            post.products.set(product_ids)
        return post

    def update(self, instance, validated_data):
        # product_ids가 명시되면(누락 아님) 태그 전체 교체. 빈 배열이면 태그 해제.
        product_ids = validated_data.pop('product_ids', None)
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()
        if product_ids is not None:
            instance.products.set(product_ids)
        return instance
