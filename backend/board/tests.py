import uuid

from django.contrib.auth.models import User
from django.test import TestCase
from rest_framework.test import APIClient

from accounts.models import UserInfo
from products.models import Product
from .models import Post, Comment, PostLike


def _make_product(**overrides):
    defaults = dict(
        brand='코스알엑스', name='AHA/BHA 토너', price=12000,
        oliveyoung_url='https://oliveyoung.co.kr/p', image_url='https://img/p.jpg',
        category='토너', ai_summary='여드름 진정에 좋은 토너',
        average_rating=4.6, review_count=1284,
    )
    defaults.update(overrides)
    return Product.objects.create(**defaults)


class BoardTestBase(TestCase):
    def setUp(self):
        self.user = User.objects.create(username='kakao_1')
        self.user_info = UserInfo.objects.create(
            user=self.user, email='alice@kakao.com', auth_provider='kakao',
        )
        # 타인(IDOR 검증용)
        self.other = User.objects.create(username='kakao_2')
        self.other_info = UserInfo.objects.create(
            user=self.other, email='bob@kakao.com', auth_provider='kakao',
        )
        self.client = APIClient()
        self.client.force_authenticate(user=self.user)

    def _make_post(self, owner=None, **overrides):
        defaults = dict(
            user=owner or self.user_info, category='free',
            title='제목', content='본문',
        )
        defaults.update(overrides)
        return Post.objects.create(**defaults)


# ──────────────────────────────────────────────
# 게시글 — /api/v1/posts/
# ──────────────────────────────────────────────

class PostApiTest(BoardTestBase):
    def test_list_is_paginated(self):
        for i in range(3):
            self._make_post(title=f'글{i}')
        res = self.client.get('/api/v1/posts/')
        self.assertEqual(res.status_code, 200)
        self.assertIn('results', res.data)         # 페이지네이션 형식
        self.assertEqual(res.data['count'], 3)

    def test_list_filters_by_category(self):
        self._make_post(category='free')
        self._make_post(category='sale')
        self._make_post(category='sale')
        res = self.client.get('/api/v1/posts/?category=sale')
        self.assertEqual(res.data['count'], 2)

    def test_create_post(self):
        res = self.client.post('/api/v1/posts/', {
            'category': 'qna', 'title': '여드름 토너 질문', 'content': '추천해주세요',
        }, format='json')
        self.assertEqual(res.status_code, 201)
        self.assertEqual(res.data['title'], '여드름 토너 질문')
        self.assertEqual(res.data['category_label'], 'Q&A·팁')
        self.assertEqual(res.data['author'], 'alice')      # 이메일 로컬파트
        self.assertEqual(Post.objects.count(), 1)
        # user가 서버에서 강제 주입됐는지
        self.assertEqual(Post.objects.first().user, self.user_info)

    def test_create_post_with_product_tag(self):
        product = _make_product()
        res = self.client.post('/api/v1/posts/', {
            'category': 'sale', 'title': '이거 세일중', 'content': '올영 50%',
            'product_id': str(product.id),
        }, format='json')
        self.assertEqual(res.status_code, 201)
        self.assertEqual(res.data['product']['id'], str(product.id))   # 제품 카드 중첩
        self.assertEqual(Post.objects.first().product, product)

    def test_create_post_with_invalid_product_is_rejected(self):
        res = self.client.post('/api/v1/posts/', {
            'category': 'free', 'title': 't', 'content': 'c',
            'product_id': str(uuid.uuid4()),
        }, format='json')
        self.assertEqual(res.status_code, 400)
        self.assertEqual(Post.objects.count(), 0)

    def test_detail_includes_comments_and_product(self):
        product = _make_product()
        post = self._make_post(product=product)
        Comment.objects.create(post=post, user=self.other_info, content='댓글이요')
        res = self.client.get(f'/api/v1/posts/{post.id}/')
        self.assertEqual(res.status_code, 200)
        self.assertEqual(res.data['content'], '본문')
        self.assertEqual(len(res.data['comments']), 1)
        self.assertEqual(res.data['comments'][0]['author'], 'bob')
        self.assertEqual(res.data['product']['id'], str(product.id))

    def test_author_can_update_own_post(self):
        post = self._make_post(title='원본')
        res = self.client.patch(f'/api/v1/posts/{post.id}/', {'title': '수정됨'}, format='json')
        self.assertEqual(res.status_code, 200)
        self.assertEqual(res.data['title'], '수정됨')

    def test_non_author_cannot_update(self):
        post = self._make_post(owner=self.other_info)   # 타인 글
        res = self.client.patch(f'/api/v1/posts/{post.id}/', {'title': '훔침'}, format='json')
        self.assertEqual(res.status_code, 403)

    def test_author_can_delete_own_post(self):
        post = self._make_post()
        res = self.client.delete(f'/api/v1/posts/{post.id}/')
        self.assertEqual(res.status_code, 204)
        self.assertEqual(Post.objects.count(), 0)

    def test_non_author_cannot_delete(self):
        post = self._make_post(owner=self.other_info)
        res = self.client.delete(f'/api/v1/posts/{post.id}/')
        self.assertEqual(res.status_code, 403)
        self.assertEqual(Post.objects.count(), 1)

    def test_requires_auth(self):
        res = APIClient().get('/api/v1/posts/')
        self.assertIn(res.status_code, (401, 403))


# ──────────────────────────────────────────────
# 댓글 — /api/v1/posts/<uuid>/comments/, /api/v1/comments/<id>/
# ──────────────────────────────────────────────

class CommentApiTest(BoardTestBase):
    def test_create_comment(self):
        post = self._make_post()
        res = self.client.post(f'/api/v1/posts/{post.id}/comments/',
                               {'content': '좋은 글이네요'}, format='json')
        self.assertEqual(res.status_code, 201)
        self.assertEqual(res.data['content'], '좋은 글이네요')
        self.assertEqual(Comment.objects.count(), 1)

    def test_empty_comment_rejected(self):
        post = self._make_post()
        res = self.client.post(f'/api/v1/posts/{post.id}/comments/',
                               {'content': '   '}, format='json')
        self.assertEqual(res.status_code, 400)

    def test_author_can_delete_own_comment(self):
        post = self._make_post()
        comment = Comment.objects.create(post=post, user=self.user_info, content='c')
        res = self.client.delete(f'/api/v1/comments/{comment.id}/')
        self.assertEqual(res.status_code, 204)

    def test_cannot_delete_others_comment(self):
        post = self._make_post()
        comment = Comment.objects.create(post=post, user=self.other_info, content='남의 댓글')
        res = self.client.delete(f'/api/v1/comments/{comment.id}/')
        self.assertEqual(res.status_code, 404)            # IDOR 차단(존재 노출 안 함)
        self.assertEqual(Comment.objects.count(), 1)


# ──────────────────────────────────────────────
# 좋아요 — /api/v1/posts/<uuid>/like/
# ──────────────────────────────────────────────

class PostLikeApiTest(BoardTestBase):
    def test_like_and_idempotent(self):
        post = self._make_post()
        res1 = self.client.post(f'/api/v1/posts/{post.id}/like/')
        self.assertEqual(res1.status_code, 201)
        self.assertEqual(res1.data['like_count'], 1)
        # 두 번 눌러도 멱등(중복 생성 안 됨)
        res2 = self.client.post(f'/api/v1/posts/{post.id}/like/')
        self.assertEqual(res2.status_code, 200)
        self.assertEqual(PostLike.objects.count(), 1)

    def test_unlike(self):
        post = self._make_post()
        PostLike.objects.create(user=self.user_info, post=post)
        res = self.client.delete(f'/api/v1/posts/{post.id}/like/')
        self.assertEqual(res.status_code, 200)
        self.assertEqual(res.data['like_count'], 0)
        self.assertEqual(PostLike.objects.count(), 0)

    def test_unlike_when_not_liked_returns_404(self):
        post = self._make_post()
        res = self.client.delete(f'/api/v1/posts/{post.id}/like/')
        self.assertEqual(res.status_code, 404)


# ──────────────────────────────────────────────
# 역참조 — /api/v1/products/<uuid>/posts/
# ──────────────────────────────────────────────

class ProductPostsTest(BoardTestBase):
    def test_returns_posts_tagged_with_product(self):
        product = _make_product()
        other_product = _make_product(name='다른 제품')
        self._make_post(product=product, title='이 제품 후기')
        self._make_post(product=product, title='이 제품 질문', category='qna')
        self._make_post(product=other_product, title='무관한 글')
        self._make_post(title='태그 없는 글')

        res = self.client.get(f'/api/v1/products/{product.id}/posts/')
        self.assertEqual(res.status_code, 200)
        self.assertEqual(res.data['count'], 2)            # 그 제품 태그된 2건만
        titles = {p['title'] for p in res.data['results']}
        self.assertEqual(titles, {'이 제품 후기', '이 제품 질문'})

    def test_unknown_product_returns_404(self):
        res = self.client.get(f'/api/v1/products/{uuid.uuid4()}/posts/')
        self.assertEqual(res.status_code, 404)
