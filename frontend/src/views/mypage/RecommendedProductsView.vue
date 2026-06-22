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
    <div class="page-header">
      <div>
        <h2 class="page-title">추천받은 제품</h2>
        <p class="page-desc">챗봇이 추천해 준 제품을 추천받은 순서대로 모아봤어요.</p>
      </div>
      <span class="count">총 {{ totalCount }}개</span>
    </div>

    <p v-if="errorMsg" class="error-msg">{{ errorMsg }}</p>
    <p v-if="loading" class="loading-msg">추천 내역을 불러오는 중...</p>

    <!-- 배치 타임라인 -->
    <div v-if="batches.length" class="timeline">
      <section v-for="batch in batches" :key="batch.id" class="batch">
        <div class="batch-head">
          <p class="batch-summary">{{ batch.content }}</p>
          <span class="batch-date">{{ formatDate(batch.created_at) }}</span>
        </div>

        <div class="product-grid">
          <div v-for="product in batch.products" :key="`${batch.id}-${product.id}`" class="product-card">
            <div class="product-image clickable" @click="productDetail.open(product)">
              <img v-if="product.image" :src="product.image" :alt="product.name" />
              <div v-else class="img-placeholder">🧴</div>
            </div>
            <div class="product-body">
              <div class="clickable" @click="productDetail.open(product)">
                <p class="brand">{{ product.brand }}</p>
                <p class="name">{{ product.name }}</p>
              </div>
              <p v-if="product.reason" class="reason">💡 {{ product.reason }}</p>
              <div class="row">
                <p class="price">{{ formatPrice(product.price) }}</p>
                <div class="actions">
                  <button
                    class="action-btn"
                    :class="{ liked: likes.isLiked(product.id) }"
                    @click="likes.toggleLike(product)"
                    title="찜하기"
                  >{{ likes.isLiked(product.id) ? '♥' : '♡' }}</button>
                  <a :href="product.oliveyoungUrl" target="_blank" class="action-btn" title="올리브영">↗</a>
                </div>
              </div>
            </div>
          </div>
        </div>
      </section>
    </div>

    <div v-else-if="!loading" class="empty">
      <p class="empty-icon">💬</p>
      <p class="empty-text">아직 추천받은 제품이 없어요.</p>
      <p class="empty-sub">챗봇에게 화장품을 추천받아 보세요.</p>
    </div>
  </div>
</template>

<style scoped>
.view { width: 100%; max-width: 720px; margin: 0 auto; }

.page-header {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  margin-bottom: 24px;
}
.page-title { font-size: 21px; font-weight: 800; letter-spacing: -0.4px; margin-bottom: 4px; }
.page-desc { font-size: 13px; color: var(--text-secondary); }
.count {
  font-size: 12px;
  font-weight: 600;
  color: var(--brand);
  background: var(--brand-soft);
  padding: 4px 12px;
  border-radius: 999px;
  white-space: nowrap;
}

.error-msg { font-size: 13px; color: var(--danger); margin-bottom: 12px; }
.loading-msg { font-size: 13px; color: var(--text-muted); padding: 40px 0; text-align: center; }

/* 배치 타임라인 */
.timeline { display: flex; flex-direction: column; gap: 28px; }
.batch {
  display: flex;
  flex-direction: column;
  gap: 12px;
  animation: bt-rise 0.5s var(--ease) both;
}
.batch:nth-child(2) { animation-delay: 0.08s; }
.batch:nth-child(3) { animation-delay: 0.16s; }
.batch:nth-child(n+4) { animation-delay: 0.24s; }
.batch-head {
  position: relative;
  display: flex;
  align-items: baseline;
  justify-content: space-between;
  gap: 12px;
  padding-bottom: 10px;
  padding-left: 14px;
  border-bottom: 1px solid var(--border);
}
.batch-head::before {
  content: '';
  position: absolute;
  left: 0;
  top: 2px;
  width: 4px;
  height: 1.1em;
  border-radius: 999px;
  background: var(--gradient-brand);
}
.batch-summary { font-size: 14px; font-weight: 700; line-height: 1.5; letter-spacing: -0.2px; }
.batch-date { font-size: 12px; color: var(--text-muted); white-space: nowrap; }

.product-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(220px, 1fr));
  gap: 14px;
}

.product-card {
  background: var(--surface);
  border-radius: var(--radius-lg);
  overflow: hidden;
  border: 1px solid var(--border);
  box-shadow: var(--shadow-sm);
  transition: transform var(--t) var(--ease), box-shadow var(--t) var(--ease);
  display: flex;
  flex-direction: column;
}
.product-card:hover { transform: translateY(-3px); box-shadow: var(--shadow-md); }

.product-image {
  width: 100%;
  aspect-ratio: 1;
  background: var(--surface-hover);
  display: flex;
  align-items: center;
  justify-content: center;
  overflow: hidden;
}
.product-image img {
  width: 100%;
  height: 100%;
  object-fit: cover;
  transition: transform var(--t-slow) var(--ease);
}
.product-card:hover .product-image img { transform: scale(1.06); }
.clickable { cursor: pointer; }
.product-body .clickable:hover .name { text-decoration: underline; }
.img-placeholder { font-size: 48px; }

.product-body { padding: 12px 14px; display: flex; flex-direction: column; gap: 6px; flex: 1; }
.brand { font-size: 11px; color: var(--text-muted); }
.name { font-size: 14px; font-weight: 500; line-height: 1.4; }
.reason {
  font-size: 12px;
  line-height: 1.5;
  color: var(--text-secondary);
  background: var(--brand-soft);
  border-radius: var(--radius-sm);
  padding: 8px 10px;
}

.row { display: flex; align-items: center; justify-content: space-between; margin-top: auto; padding-top: 4px; }
.price { font-size: 13px; color: var(--text-secondary); }

.actions { display: flex; gap: 4px; }
.action-btn {
  width: 28px;
  height: 28px;
  border-radius: var(--radius-sm);
  border: 1px solid var(--border);
  background: var(--surface);
  font-size: 13px;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  text-decoration: none;
  color: var(--text-secondary);
  transition: background var(--t-fast) var(--ease), transform var(--t-fast) var(--ease-back), border-color var(--t-fast) var(--ease), color var(--t-fast) var(--ease);
}
.action-btn:hover { background: var(--surface-hover); transform: translateY(-1px); }
.action-btn.liked {
  color: var(--brand);
  background: var(--brand-soft);
  border-color: var(--brand-1);
  animation: bt-pop var(--t) var(--ease-back);
}
.action-btn.liked:hover { box-shadow: var(--shadow-glow); }

.empty {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 8px;
  padding: 60px 0;
  text-align: center;
}
.empty-icon { font-size: 40px; }
.empty-text { font-size: 15px; font-weight: 500; }
.empty-sub { font-size: 13px; color: var(--text-muted); }
</style>
