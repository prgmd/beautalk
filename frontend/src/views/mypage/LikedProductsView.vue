<script setup>
import { computed, onMounted, ref } from 'vue'
import { useLikesStore } from '@/stores/likes'
import { useProductDetailStore } from '@/stores/productDetail'
import { useToastStore } from '@/stores/toast'
import Icon from '@/components/Icon.vue'

const likes = useLikesStore()
const productDetail = useProductDetailStore()
const toast = useToastStore()

const likedProducts = computed(() => likes.items)
const loading = ref(false)
const loadError = ref(false)

// 진입 시 백엔드에서 최신 찜 목록을 불러온다(이미 불러왔으면 생략).
onMounted(async () => {
  if (likes.loaded) return
  loading.value = true
  loadError.value = false
  try {
    await likes.fetchLikes()
  } catch {
    // 캐시가 없으면 사용자에게 알린다(빈 상태로 오인 방지).
    if (!likes.items.length) loadError.value = true
  }
  loading.value = false
})

function retry() {
  loadError.value = false
  likes.loaded = false
  onLoad()
}
async function onLoad() {
  loading.value = true
  try { await likes.fetchLikes() } catch { if (!likes.items.length) loadError.value = true }
  loading.value = false
}

function formatPrice(n) {
  return n != null ? n.toLocaleString('ko-KR') + '원' : '가격 정보 없음'
}

function unlike(product) {
  likes.toggleLike(product)
  toast.show('찜을 해제했어요')
}
</script>

<template>
  <div class="view">
    <header class="page-header">
      <p class="eyebrow">My Collection</p>
      <div class="title-row">
        <h2 class="page-title serif">찜한 제품</h2>
        <span class="count">총 {{ likedProducts.length }}개</span>
      </div>
    </header>

    <div v-if="loading && !likedProducts.length" class="product-grid" aria-hidden="true">
      <article v-for="n in 6" :key="n" class="product-card skel">
        <div class="product-image sk" />
        <div class="product-body">
          <div class="sk-line sk" style="width:40%" />
          <div class="sk-line sk" style="width:80%" />
          <div class="sk-line sk" style="width:55%" />
        </div>
      </article>
    </div>

    <div v-else-if="loadError && !likedProducts.length" class="empty">
      <span class="empty-art"><Icon name="leaf" :size="40" /></span>
      <p class="empty-text serif">불러오지 못했어요.</p>
      <button class="retry-btn" @click="retry">다시 시도</button>
    </div>

    <div v-if="likedProducts.length" class="product-grid">
      <article v-for="(product, i) in likedProducts" :key="product.id" class="product-card" :style="{ '--d': i * 40 + 'ms' }">
        <div class="product-image clickable" @click="productDetail.open(product)">
          <img v-if="product.image" :src="product.image" :alt="product.name" />
          <Icon v-else name="leaf" :size="36" class="img-placeholder" />
        </div>
        <div class="product-body">
          <div class="clickable" @click="productDetail.open(product)">
            <p class="brand">{{ product.brand }}</p>
            <p class="name">{{ product.name }}</p>
          </div>
          <div class="row">
            <p class="price serif">{{ formatPrice(product.price) }}</p>
            <div class="actions">
              <a
                v-if="product.oliveyoungUrl && product.oliveyoungUrl !== '#'"
                :href="product.oliveyoungUrl" target="_blank" rel="noopener noreferrer"
                class="link-btn" aria-label="올리브영에서 보기"><Icon name="external" :size="14" /></a>
              <button class="heart liked" aria-label="찜 해제" @click="unlike(product)"><Icon name="heart-fill" :size="15" /></button>
            </div>
          </div>
        </div>
      </article>
    </div>

    <div v-else-if="!loading && !loadError" class="empty">
      <span class="empty-art"><Icon name="leaf" :size="40" /></span>
      <p class="empty-text serif">아직 찜한 제품이 없어요.</p>
      <p class="empty-sub">챗봇에서 마음에 드는 제품에 <em>♡</em>를 눌러보세요.</p>
    </div>
  </div>
</template>

<style scoped>
.view { width: 100%; }

/* Header */
.page-header { margin-bottom: 20px; animation: bt-rise 0.5s var(--ease) both; }
.eyebrow {
  font-size: 11px;
  font-weight: 600;
  letter-spacing: 0.18em;
  text-transform: uppercase;
  color: var(--ink-faint);
  margin-bottom: 6px;
}
.title-row { display: flex; align-items: center; gap: 12px; }
.page-title { font-size: 25px; font-weight: 600; letter-spacing: -0.4px; color: var(--ink); }
.count {
  font-size: 12px;
  font-weight: 600;
  color: var(--sage-ink);
  background: var(--sage-soft);
  border: 1px solid var(--line-soft);
  padding: 4px 12px;
  border-radius: 999px;
  white-space: nowrap;
}

/* Skeleton */
.skel { pointer-events: none; animation: none; }
.sk { position: relative; overflow: hidden; background: var(--panel); }
.sk::after {
  content: '';
  position: absolute;
  inset: 0;
  background: linear-gradient(100deg, transparent 20%, rgba(255,255,255,.65) 50%, transparent 80%);
  transform: translateX(-100%);
  animation: shimmer 1.3s infinite;
}
.sk-line { height: 11px; border-radius: 6px; margin: 7px 0; }
@keyframes shimmer { 100% { transform: translateX(100%); } }

/* Grid: 2-column arch cards */
.product-grid {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 14px;
}

.product-card {
  background: var(--card);
  border-radius: var(--radius-lg);
  overflow: hidden;
  border: 1px solid var(--line-soft);
  box-shadow: var(--sh-soft);
  transition: transform var(--t) var(--ease), box-shadow var(--t) var(--ease);
  animation: card-in 0.5s var(--ease) both;
  animation-delay: var(--d, 0ms);
}
.product-card:active { transform: scale(0.985); box-shadow: var(--sh-soft); }
@media (hover: hover) {
  .product-card:hover { transform: translateY(-4px); box-shadow: var(--sh-hover); }
}
@keyframes card-in { from { opacity: 0; transform: translateY(12px); } to { opacity: 1; transform: none; } }

/* Arch frame image */
.product-image {
  position: relative;
  width: 100%;
  aspect-ratio: 0.86;
  margin: 8px 8px 0;
  width: calc(100% - 16px);
  border-radius: 110px 110px 12px 12px;
  background: linear-gradient(170deg, #EFE7DB, #E6E3D0 60%, #DEE7DF);
  display: flex;
  align-items: center;
  justify-content: center;
  overflow: hidden;
}
.product-image img {
  width: 100%;
  height: 100%;
  object-fit: cover;
  transition: transform .6s var(--ease);
}
@media (hover: hover) {
  .product-card:hover .product-image img { transform: scale(1.05); }
}
.clickable { cursor: pointer; }
.product-body .clickable:hover .name { text-decoration: underline; }
.img-placeholder { color: var(--sage); opacity: .5; position: relative; z-index: 1; }

.product-body { padding: 12px 14px 14px; display: flex; flex-direction: column; gap: 4px; }
.brand {
  font-size: 10px;
  font-weight: 600;
  letter-spacing: 0.12em;
  text-transform: uppercase;
  color: var(--ink-faint);
}
.name { font-size: 13.5px; font-weight: 500; line-height: 1.4; color: var(--ink); }

.row { display: flex; align-items: center; justify-content: space-between; gap: 8px; margin-top: 6px; }
.price { font-size: 15px; font-weight: 600; color: var(--ink); white-space: nowrap; }

.actions { display: flex; align-items: center; gap: 6px; }
.link-btn {
  width: 30px; height: 30px;
  border-radius: 50%;
  border: 1px solid var(--line);
  background: var(--sheet);
  font-size: 13px;
  display: flex;
  align-items: center;
  justify-content: center;
  text-decoration: none;
  color: var(--ink-soft);
  transition: background var(--t-fast) var(--ease), transform var(--t-fast) var(--ease-back);
}
.link-btn:active { transform: scale(0.92); }
@media (hover: hover) {
  .link-btn:hover { background: var(--panel); transform: translateY(-1px); }
}

/* Heart: white circle + rose; .liked = rose bg + white */
.heart {
  width: 30px; height: 30px;
  border-radius: 50%;
  border: 1px solid var(--line);
  background: var(--card);
  color: var(--rose);
  font-size: 14px;
  line-height: 1;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: background var(--t-fast) var(--ease), transform var(--t-fast) var(--ease-back), color var(--t-fast) var(--ease);
}
.heart:active { transform: scale(0.9); }
.heart.liked {
  background: var(--rose);
  border-color: var(--rose);
  color: #fff;
  box-shadow: var(--sh-bub);
}

/* Empty */
.empty {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 8px;
  padding: 64px 24px;
  text-align: center;
  animation: bt-rise 0.5s var(--ease) both;
}
.empty-art {
  width: 72px; height: 72px; border-radius: 50%;
  display: flex; align-items: center; justify-content: center;
  background: var(--sage-soft); color: var(--sage-ink);
}
.empty-text { font-size: 18px; font-weight: 600; color: var(--ink); }
.empty-sub { font-size: 13px; color: var(--ink-soft); line-height: 1.6; }
.empty-sub em { color: var(--rose); font-style: normal; }
.retry-btn {
  margin-top: 6px; padding: 10px 22px; border-radius: 99px; font-size: 13.5px; font-weight: 600;
  color: var(--ink); background: var(--card); border: 1px solid var(--line); box-shadow: var(--sh-sm);
}

@media (prefers-reduced-motion: reduce) {
  .product-card { animation: none; }
  .sk::after { animation: none; }
  .product-card:hover .product-image img { transform: none; }
}

/* ===== Desktop (≥900px) ===== */
@media (min-width: 900px) {
  .view { max-width: 900px; }

  .page-header { margin-bottom: 28px; }
  .page-title { font-size: 30px; }

  /* 3-column arch-card grid */
  .product-grid {
    grid-template-columns: repeat(3, 1fr);
    gap: 20px;
  }

  .empty { padding: 88px 24px; }
}
</style>
