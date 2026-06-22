<script setup>
import { computed } from 'vue'
import { useChatStore } from '@/stores/chat'
import { useProductDetailStore } from '@/stores/productDetail'

const chat = useChatStore()
const productDetail = useProductDetailStore()

const products = computed(() => chat.recommendedProducts)

function formatPrice(n) {
  return n.toLocaleString('ko-KR') + '원'
}

function relativeTime(dateStr) {
  const diff = Date.now() - new Date(dateStr).getTime()
  const h = Math.floor(diff / 3600000)
  const d = Math.floor(diff / 86400000)
  if (h < 1) return '방금 전'
  if (h < 24) return `${h}시간 전`
  return `${d}일 전`
}
</script>

<template>
  <div class="view">
    <div class="page-header">
      <div>
        <h2 class="page-title">추천받은 제품</h2>
        <p class="page-desc">챗봇이 추천해 준 제품을 모아봤어요.</p>
      </div>
      <span class="count">총 {{ products.length }}개</span>
    </div>

    <div v-if="products.length" class="product-grid">
      <div v-for="product in products" :key="product.id" class="product-card">
        <div class="product-image clickable" @click="productDetail.open(product)">
          <div class="img-placeholder">🧴</div>
        </div>
        <div class="product-body">
          <div class="clickable" @click="productDetail.open(product)">
            <p class="brand">{{ product.brand }}</p>
            <p class="name">{{ product.name }}</p>
          </div>
          <div class="row">
            <p class="price">{{ formatPrice(product.price) }}</p>
            <div class="actions">
              <button
                class="action-btn"
                :class="{ liked: chat.isLiked(product.id) }"
                @click="chat.toggleLike(product)"
                title="찜하기"
              >{{ chat.isLiked(product.id) ? '♥' : '♡' }}</button>
              <a :href="product.oliveyoungUrl" target="_blank" class="action-btn" title="올리브영">↗</a>
            </div>
          </div>
          <p class="recommended-at">{{ relativeTime(product.recommendedAt) }} 추천</p>
        </div>
      </div>
    </div>

    <div v-else class="empty">
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
}
.product-card:hover { box-shadow: 0 4px 16px rgba(0,0,0,0.08); }

.product-image {
  width: 100%;
  aspect-ratio: 1;
  background: var(--surface-hover);
  display: flex;
  align-items: center;
  justify-content: center;
}
.clickable { cursor: pointer; }
.product-body .clickable:hover .name { text-decoration: underline; }
.img-placeholder { font-size: 48px; }

.product-body { padding: 12px 14px; display: flex; flex-direction: column; gap: 4px; }
.brand { font-size: 11px; color: var(--text-muted); }
.name { font-size: 14px; font-weight: 500; line-height: 1.4; }

.row { display: flex; align-items: center; justify-content: space-between; margin-top: 4px; }
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

.recommended-at { font-size: 11px; color: var(--text-muted); margin-top: 2px; }

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
