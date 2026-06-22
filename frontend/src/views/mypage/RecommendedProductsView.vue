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
.page-title { font-size: 20px; font-weight: 700; margin-bottom: 4px; }
.page-desc { font-size: 13px; color: var(--text-secondary); }
.count { font-size: 13px; color: var(--text-muted); white-space: nowrap; }

.error-msg { font-size: 13px; color: var(--danger); margin-bottom: 12px; }
.loading-msg { font-size: 13px; color: var(--text-muted); padding: 40px 0; text-align: center; }

/* 배치 타임라인 */
.timeline { display: flex; flex-direction: column; gap: 28px; }
.batch { display: flex; flex-direction: column; gap: 12px; }
.batch-head {
  display: flex;
  align-items: baseline;
  justify-content: space-between;
  gap: 12px;
  padding-bottom: 8px;
  border-bottom: 1px solid var(--border);
}
.batch-summary { font-size: 14px; font-weight: 600; line-height: 1.5; }
.batch-date { font-size: 12px; color: var(--text-muted); white-space: nowrap; }

.product-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(220px, 1fr));
  gap: 14px;
}

.product-card {
  background: var(--bg);
  border-radius: 14px;
  overflow: hidden;
  border: 1px solid var(--border);
  transition: box-shadow 0.15s;
  display: flex;
  flex-direction: column;
}
.product-card:hover { box-shadow: 0 4px 16px rgba(0,0,0,0.08); }

.product-image {
  width: 100%;
  aspect-ratio: 1;
  background: var(--surface-hover);
  display: flex;
  align-items: center;
  justify-content: center;
  overflow: hidden;
}
.product-image img { width: 100%; height: 100%; object-fit: cover; }
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
  background: var(--surface);
  border-radius: 8px;
  padding: 8px 10px;
}

.row { display: flex; align-items: center; justify-content: space-between; margin-top: auto; padding-top: 4px; }
.price { font-size: 13px; color: var(--text-secondary); }

.actions { display: flex; gap: 4px; }
.action-btn {
  width: 28px;
  height: 28px;
  border-radius: 6px;
  border: 1px solid var(--border);
  background: var(--surface);
  font-size: 13px;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  text-decoration: none;
  color: var(--text-secondary);
  transition: background 0.15s;
}
.action-btn:hover { background: var(--surface-hover); }
.action-btn.liked { color: #E53935; border-color: #FECACA; }

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
