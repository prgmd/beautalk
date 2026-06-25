import { createRouter, createWebHistory } from 'vue-router'
import { useAuthStore } from '@/stores/auth'

const router = createRouter({
  history: createWebHistory(import.meta.env.BASE_URL),
  scrollBehavior: () => ({ top: 0 }),
  routes: [
    {
      path: '/',
      redirect: '/home',
    },
    {
      path: '/home',
      name: 'home',
      component: () => import('@/views/DashboardView.vue'),
      meta: { requiresAuth: true },
    },
    {
      path: '/consult',
      name: 'consult',
      component: () => import('@/views/ConsultHubView.vue'),
      meta: { requiresAuth: true },
    },
    {
      path: '/consult/skin',
      name: 'consult-skin',
      component: () => import('@/views/SkinConsultView.vue'),
      meta: { requiresAuth: true },
    },
    {
      path: '/login',
      name: 'login',
      component: () => import('@/views/LoginView.vue'),
      meta: { guest: true },
    },
    {
      path: '/onboarding',
      name: 'onboarding',
      component: () => import('@/views/OnboardingView.vue'),
      meta: { requiresAuth: true },
    },
    {
      path: '/chat',
      name: 'chat',
      component: () => import('@/views/ChatView.vue'),
      meta: { requiresAuth: true },
    },
    {
      path: '/catalog',
      name: 'catalog',
      component: () => import('@/views/CatalogView.vue'),
      meta: { requiresAuth: true },
    },
    {
      path: '/community',
      name: 'community',
      component: () => import('@/views/community/CommunityView.vue'),
      meta: { requiresAuth: true },
    },
    {
      path: '/community/new',
      name: 'community-new',
      component: () => import('@/views/community/PostEditorView.vue'),
      meta: { requiresAuth: true },
    },
    {
      path: '/community/:id',
      name: 'community-detail',
      component: () => import('@/views/community/PostDetailView.vue'),
      meta: { requiresAuth: true },
    },
    {
      path: '/community/:id/edit',
      name: 'community-edit',
      component: () => import('@/views/community/PostEditorView.vue'),
      meta: { requiresAuth: true },
    },
    {
      path: '/mypage',
      component: () => import('@/views/mypage/MyPageLayout.vue'),
      meta: { requiresAuth: true },
      children: [
        { path: '', redirect: '/mypage/profile' },
        { path: 'profile', name: 'mypage-profile', component: () => import('@/views/mypage/SkinProfileView.vue') },
        { path: 'liked', name: 'mypage-liked', component: () => import('@/views/mypage/LikedProductsView.vue') },
        { path: 'recommended', name: 'mypage-recommended', component: () => import('@/views/mypage/RecommendedProductsView.vue') },
        { path: 'account', name: 'mypage-account', component: () => import('@/views/mypage/AccountView.vue') },
      ],
    },
    {
      // 로그인 callback 경로 추가
      path: '/auth/callback',
      name: 'auth-callback',
      component: () => import('@/views/AuthCallbackView.vue'),
    },
  ],
})

router.beforeEach((to) => {
  const auth = useAuthStore()
  if (to.meta.requiresAuth && !auth.isLoggedIn) return '/login'
  if (to.meta.guest && auth.isLoggedIn) return '/home'
})

export default router
