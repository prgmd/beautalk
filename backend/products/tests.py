from django.contrib.auth.models import User
from django.test import TestCase
from rest_framework.test import APIClient

from accounts.models import UserInfo
from .models import Product, Like


class LikeApiTest(TestCase):
    """찜 추가/조회/삭제 + 소유권 격리(IDOR 방어) 검증"""

    def setUp(self):
        self.user = User.objects.create(username='kakao_1')
        self.user_info = UserInfo.objects.create(
            user=self.user, email='a@kakao.com', auth_provider='kakao',
        )
        self.product = Product.objects.create(
            brand='브랜드', name='수분크림', price=12000,
            oliveyoung_url='https://oliveyoung.co.kr/p/1',
            image_url='https://img/1.jpg', category='스킨케어',
        )
        self.client = APIClient()
        self.client.force_authenticate(user=self.user)

    def test_add_like(self):
        res = self.client.post('/api/v1/likes/', {'product_id': str(self.product.id)}, format='json')
        self.assertEqual(res.status_code, 201)
        self.assertEqual(res.data['product']['name'], '수분크림')
        self.assertTrue(Like.objects.filter(user=self.user_info, product=self.product).exists())

    def test_add_like_is_idempotent(self):
        # 같은 제품을 두 번 찜해도 500이 아니라 200으로 멱등 처리
        self.client.post('/api/v1/likes/', {'product_id': str(self.product.id)}, format='json')
        res = self.client.post('/api/v1/likes/', {'product_id': str(self.product.id)}, format='json')
        self.assertEqual(res.status_code, 200)
        self.assertEqual(Like.objects.filter(user=self.user_info).count(), 1)

    def test_list_likes_with_product_info(self):
        Like.objects.create(user=self.user_info, product=self.product)
        res = self.client.get('/api/v1/likes/')
        self.assertEqual(res.status_code, 200)
        self.assertEqual(len(res.data), 1)
        self.assertEqual(res.data[0]['product']['oliveyoung_url'], 'https://oliveyoung.co.kr/p/1')

    def test_delete_like(self):
        Like.objects.create(user=self.user_info, product=self.product)
        res = self.client.delete(f'/api/v1/likes/{self.product.id}/')
        self.assertEqual(res.status_code, 204)
        self.assertFalse(Like.objects.filter(user=self.user_info).exists())

    def test_cannot_delete_others_like(self):
        # 타인의 찜은 삭제되지 않아야 한다 (IDOR 차단)
        other = User.objects.create(username='kakao_2')
        other_info = UserInfo.objects.create(user=other, email='b@kakao.com', auth_provider='kakao')
        Like.objects.create(user=other_info, product=self.product)

        res = self.client.delete(f'/api/v1/likes/{self.product.id}/')
        self.assertEqual(res.status_code, 404)
        self.assertTrue(Like.objects.filter(user=other_info).exists())

    def test_requires_auth(self):
        anon = APIClient()
        res = anon.get('/api/v1/likes/')
        self.assertIn(res.status_code, (401, 403))


class ProductApiTest(TestCase):
    def setUp(self):
        self.user = User.objects.create(username='kakao_1')
        UserInfo.objects.create(user=self.user, email='a@kakao.com', auth_provider='kakao')
        Product.objects.create(
            brand='B', name='클렌징폼', price=9000,
            oliveyoung_url='https://o/2', image_url='https://i/2', category='클렌징',
        )
        self.client = APIClient()
        self.client.force_authenticate(user=self.user)

    def test_list_is_paginated(self):
        res = self.client.get('/api/v1/products/')
        self.assertEqual(res.status_code, 200)
        # DEFAULT_PAGINATION_CLASS 적용 → results 키로 감싸진다
        self.assertIn('results', res.data)

    def test_category_filter(self):
        res = self.client.get('/api/v1/products/?category=클렌징')
        self.assertEqual(res.data['count'], 1)
        res2 = self.client.get('/api/v1/products/?category=없는카테고리')
        self.assertEqual(res2.data['count'], 0)
