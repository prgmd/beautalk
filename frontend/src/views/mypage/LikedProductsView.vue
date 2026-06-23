<script setup>
import { computed, onMounted, ref } from 'vue'
import { useLikesStore } from '@/stores/likes'
import { useProductDetailStore } from '@/stores/productDetail'

const likes = useLikesStore()
const productDetail = useProductDetailStore()

const likedProducts = computed(() => likes.items)
const loading = ref(false)

// 진입 시 백엔드에서 최신 찜 목록을 불러온다(이미 불러왔으면 생략).
onMounted(async () => {
  if (likes.loaded) return
  loading.value = true
  try {
    await likes.fetchLikes()
  } catch {
    // 실패해도 로컬 캐시로 계속 표시한다.
  }
  loading.value = false
})

function formatPrice(n) {
  return n?.toLocaleString('ko-KR') + '원'
}

function unlike(product) {
  likes.toggleLike(product)
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

    <p v-if="loading && !likedProducts.length" class="loading-msg">
      <span class="dots"><i></i><i></i><i></i></span>
      찜한 제품을 불러오는 중...
    </p>

    <div v-if="likedProducts.length" class="product-grid">
      <article v-for="product in likedProducts" :key="product.id" class="product-card">
        <div class="product-image clickable" @click="productDetail.open(product)">
          <img v-if="product.image" :src="product.image" :alt="product.name" />
          <div v-else class="img-placeholder">🧴</div>
        </div>
        <div class="product-body">
          <div class="clickable" @click="productDetail.open(product)">
            <p class="brand">{{ product.brand }}</p>
            <p class="name">{{ product.name }}</p>
          </div>
          <div class="row">
            <p class="price serif">{{ formatPrice(product.price) }}</p>
            <div class="actions">
              <a :href="product.oliveyoungUrl" target="_blank" class="link-btn" title="올리브영">↗</a>
              <button class="heart liked" @click="unlike(product)" title="찜 해제">♥</button>
            </div>
          </div>
        </div>
      </article>
    </div>

    <div v-else-if="!loading" class="empty">
      <p class="empty-icon">🤍</p>
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

.loading-msg {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 12px;
  font-size: 13px;
  color: var(--ink-soft);
  padding: 48px 0;
  text-align: center;
}
.dots { display: inline-flex; gap: 5px; }
.dots i {
  width: 7px; height: 7px;
  border-radius: 50%;
  background: var(--sage);
  animation: bt-pop 0.9s var(--ease) infinite;
}
.dots i:nth-child(2) { animation-delay: 0.15s; opacity: 0.7; }
.dots i:nth-child(3) { animation-delay: 0.3s; opacity: 0.45; }

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
  box-shadow: var(--sh-sm);
  transition: transform var(--t) var(--ease), box-shadow var(--t) var(--ease);
  animation: bt-rise 0.5s var(--ease) both;
}
.product-grid .product-card:nth-child(2) { animation-delay: 0.05s; }
.product-grid .product-card:nth-child(3) { animation-delay: 0.1s; }
.product-grid .product-card:nth-child(4) { animation-delay: 0.15s; }
.product-grid .product-card:nth-child(n+5) { animation-delay: 0.2s; }
.product-card:active { transform: scale(0.985); box-shadow: var(--sh-sm); }
@media (hover: hover) {
  .product-card:hover { transform: translateY(-3px); box-shadow: var(--sh-md); }
}

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
.product-image::before {
  content: '';
  position: absolute;
  left: 0; right: 0; bottom: 0;
  height: 46%;
  background: repeating-linear-gradient(180deg, transparent 0 9px, rgba(34, 42, 46, .05) 9px 10px);
  pointer-events: none;
}
.product-image img {
  width: 100%;
  height: 100%;
  object-fit: cover;
  transition: transform var(--t-slow) var(--ease);
}
@media (hover: hover) {
  .product-card:hover .product-image img { transform: scale(1.05); }
}
.clickable { cursor: pointer; }
.product-body .clickable:hover .name { text-decoration: underline; }
.img-placeholder { font-size: 46px; position: relative; z-index: 1; }

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
.empty-icon { font-size: 42px; }
.empty-text { font-size: 18px; font-weight: 600; color: var(--ink); }
.empty-sub { font-size: 13px; color: var(--ink-soft); line-height: 1.6; }
.empty-sub em { color: var(--rose); font-style: normal; }
</style>
