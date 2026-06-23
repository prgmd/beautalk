<script setup>
import { ref, onMounted, computed } from 'vue'
import { api } from '@/services/api'
import { useLikesStore } from '@/stores/likes'
import { useProductDetailStore } from '@/stores/productDetail'
import { normalizeProduct } from '@/utils/product'

const likes = useLikesStore()
const productDetail = useProductDetailStore()

const batches = ref([]) // [{ id, content, created_at, products: [정규화된 product] }]
const loading = ref(false)
const errorMsg = ref('')

const totalCount = computed(() => batches.value.reduce((sum, b) => sum + b.products.length, 0))

onMounted(async () => {
  loading.value = true
  try {
    const { data } = await api.get('/recommendations/')
    batches.value = (data || []).map((b) => ({
      id: b.id,
      content: b.content,
      created_at: b.created_at,
      products: (b.products || []).map(normalizeProduct),
    }))
  } catch {
    errorMsg.value = '추천 내역을 불러오지 못했어요.'
  }
  loading.value = false
})

function formatPrice(n) {
  return n?.toLocaleString('ko-KR') + '원'
}

function formatDate(dateStr) {
  const d = new Date(dateStr)
  if (Number.isNaN(d.getTime())) return ''
  return `${d.getFullYear()}.${String(d.getMonth() + 1).padStart(2, '0')}.${String(d.getDate()).padStart(2, '0')}`
}
</script>

<template>
  <div class="view">
    <header class="page-header">
      <p class="eyebrow">Recommendation Journal</p>
      <div class="title-row">
        <h2 class="page-title serif">추천받은 제품</h2>
        <span class="count">총 {{ totalCount }}개</span>
      </div>
      <p class="page-desc">챗봇이 추천해 준 제품을 추천받은 순서대로 모아봤어요.</p>
    </header>

    <p v-if="errorMsg" class="error-msg">{{ errorMsg }}</p>
    <p v-if="loading" class="loading-msg">
      <span class="dots"><i></i><i></i><i></i></span>
      추천 내역을 불러오는 중...
    </p>

    <!-- 배치 타임라인 -->
    <div v-if="batches.length" class="timeline">
      <section v-for="batch in batches" :key="batch.id" class="batch">
        <div class="batch-head">
          <span class="batch-node" aria-hidden="true"></span>
          <p class="batch-summary serif">{{ batch.content }}</p>
          <span class="batch-date">{{ formatDate(batch.created_at) }}</span>
        </div>

        <div class="product-grid">
          <article v-for="product in batch.products" :key="`${batch.id}-${product.id}`" class="product-card">
            <div class="product-image clickable" @click="productDetail.open(product)">
              <img v-if="product.image" :src="product.image" :alt="product.name" />
              <div v-else class="img-placeholder">🧴</div>
            </div>
            <div class="product-body">
              <div class="clickable" @click="productDetail.open(product)">
                <p class="brand">{{ product.brand }}</p>
                <p class="name">{{ product.name }}</p>
              </div>
              <p v-if="product.reason" class="reason"><span class="reason-mark">💡</span>{{ product.reason }}</p>
              <div class="row">
                <p class="price serif">{{ formatPrice(product.price) }}</p>
                <div class="actions">
                  <a :href="product.oliveyoungUrl" target="_blank" class="link-btn" title="올리브영">↗</a>
                  <button
                    class="heart"
                    :class="{ liked: likes.isLiked(product.id) }"
                    @click="likes.toggleLike(product)"
                    title="찜하기"
                  >{{ likes.isLiked(product.id) ? '♥' : '♡' }}</button>
                </div>
              </div>
            </div>
          </article>
        </div>
      </section>
    </div>

    <div v-else-if="!loading" class="empty">
      <p class="empty-icon">💬</p>
      <p class="empty-text serif">아직 추천받은 제품이 없어요.</p>
      <p class="empty-sub">챗봇에게 화장품을 추천받아 보세요.</p>
    </div>
  </div>
</template>

<style scoped>
.view { width: 100%; }

/* Header */
.page-header { margin-bottom: 24px; animation: bt-rise 0.5s var(--ease) both; }
.eyebrow {
  font-size: 11px;
  font-weight: 600;
  letter-spacing: 0.18em;
  text-transform: uppercase;
  color: var(--ink-faint);
  margin-bottom: 6px;
}
.title-row { display: flex; align-items: center; gap: 12px; margin-bottom: 6px; }
.page-title { font-size: 25px; font-weight: 600; letter-spacing: -0.4px; color: var(--ink); }
.page-desc { font-size: 13px; color: var(--ink-soft); line-height: 1.5; }
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

.error-msg { font-size: 13px; color: var(--rose-ink); margin-bottom: 12px; }
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

/* 배치 타임라인 */
.timeline {
  display: flex;
  flex-direction: column;
  gap: 30px;
  position: relative;
  padding-left: 18px;
}
/* vertical journal line */
.timeline::before {
  content: '';
  position: absolute;
  left: 3px; top: 6px; bottom: 6px;
  width: 1px;
  background: var(--line);
}
.batch {
  display: flex;
  flex-direction: column;
  gap: 14px;
  animation: bt-rise 0.5s var(--ease) both;
}
.batch:nth-child(2) { animation-delay: 0.08s; }
.batch:nth-child(3) { animation-delay: 0.16s; }
.batch:nth-child(n+4) { animation-delay: 0.24s; }

.batch-head {
  position: relative;
  display: flex;
  flex-direction: column;
  gap: 4px;
  padding-bottom: 12px;
  border-bottom: 1px solid var(--line-soft);
}
.batch-node {
  position: absolute;
  left: -18px;
  top: 4px;
  width: 9px; height: 9px;
  border-radius: 50%;
  background: var(--sage);
  border: 2px solid var(--canvas);
  box-shadow: 0 0 0 1px var(--line);
}
.batch-summary {
  font-size: 16px;
  font-weight: 600;
  line-height: 1.55;
  letter-spacing: -0.2px;
  color: var(--ink);
}
.batch-date {
  font-size: 11px;
  font-weight: 600;
  letter-spacing: 0.08em;
  color: var(--ink-faint);
}

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
  display: flex;
  flex-direction: column;
}
.product-card:active { transform: scale(0.985); }
@media (hover: hover) {
  .product-card:hover { transform: translateY(-3px); box-shadow: var(--sh-md); }
}

/* Arch frame image */
.product-image {
  position: relative;
  width: calc(100% - 16px);
  aspect-ratio: 0.86;
  margin: 8px 8px 0;
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

.product-body { padding: 12px 14px 14px; display: flex; flex-direction: column; gap: 6px; flex: 1; }
.brand {
  font-size: 10px;
  font-weight: 600;
  letter-spacing: 0.12em;
  text-transform: uppercase;
  color: var(--ink-faint);
}
.name { font-size: 13.5px; font-weight: 500; line-height: 1.4; color: var(--ink); }
.reason {
  font-size: 12px;
  line-height: 1.55;
  color: var(--sage-ink);
  background: var(--sage-soft);
  border: 1px solid var(--line-soft);
  border-radius: var(--radius-sm);
  padding: 8px 10px;
}
.reason-mark { margin-right: 4px; }

.row { display: flex; align-items: center; justify-content: space-between; gap: 8px; margin-top: auto; padding-top: 4px; }
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
  animation: bt-pop var(--t) var(--ease-back);
}

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
</style>
