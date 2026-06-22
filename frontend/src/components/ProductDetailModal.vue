<script setup>
import { computed } from 'vue'
import { useProductDetailStore } from '@/stores/productDetail'
import { useLikesStore } from '@/stores/likes'

const store = useProductDetailStore()
const likes = useLikesStore()

const product = computed(() => store.product)
const detail = computed(() => store.detail)

const satisfactionList = computed(() => {
  if (!detail.value?.satisfaction_by_type) return []
  return Object.entries(detail.value.satisfaction_by_type)
    .map(([type, value]) => ({ type, value }))
    .sort((a, b) => b.value - a.value)
})

function formatPrice(n) {
  return n?.toLocaleString('ko-KR') + '원'
}

function stars(rating) {
  const full = Math.floor(rating)
  const half = rating - full >= 0.5
  return '★'.repeat(full) + (half ? '½' : '') + '☆'.repeat(5 - full - (half ? 1 : 0))
}
</script>

<template>
  <Transition name="modal">
    <div v-if="store.isOpen" class="overlay" @click="store.close()">
      <div class="modal" @click.stop>
        <button class="close-btn" @click="store.close()">×</button>

        <!-- 상단: 이미지 + 기본 정보 -->
        <div class="head">
          <div class="image">
            <div class="img-placeholder">🧴</div>
          </div>
          <div class="head-info">
            <p class="brand">{{ product?.brand }}</p>
            <h2 class="name">{{ product?.name }}</h2>
            <div class="rating-row" v-if="detail">
              <span class="stars">{{ stars(detail.average_rating) }}</span>
              <span class="rating-num">{{ detail.average_rating }}</span>
              <span class="review-count">리뷰 {{ detail.review_count.toLocaleString('ko-KR') }}개</span>
            </div>
            <p class="price">{{ formatPrice(product?.price) }}</p>
            <div class="head-actions">
              <button
                class="like-btn"
                :class="{ liked: likes.isLiked(product?.id) }"
                @click="likes.toggleLike(product)"
              >{{ likes.isLiked(product?.id) ? '♥ 찜함' : '♡ 찜하기' }}</button>
              <a :href="product?.oliveyoungUrl" target="_blank" class="oliveyoung-btn">
                올리브영에서 보기 ↗
              </a>
            </div>
          </div>
        </div>

        <div class="body" v-if="detail">
          <!-- AI 요약 -->
          <section class="section ai-section">
            <h3 class="section-title">✨ AI 리뷰 요약</h3>
            <p class="ai-summary">{{ detail.ai_summary }}</p>
          </section>

          <!-- 피부 타입별 만족도 -->
          <section class="section">
            <h3 class="section-title">피부 타입별 만족도</h3>
            <div class="satisfaction-list">
              <div v-for="item in satisfactionList" :key="item.type" class="satisfaction-row">
                <span class="sat-type">{{ item.type }}</span>
                <div class="sat-bar"><div class="sat-fill" :style="{ width: item.value + '%' }" /></div>
                <span class="sat-value">{{ item.value }}%</span>
              </div>
            </div>
          </section>

          <!-- 리뷰 -->
          <section class="section">
            <h3 class="section-title">실제 리뷰</h3>
            <div class="review-list">
              <div v-for="review in detail.reviews" :key="review.id" class="review-card">
                <div class="review-head">
                  <span class="review-stars">{{ stars(review.rating) }}</span>
                  <span class="review-user">{{ review.user_name }}</span>
                  <span class="review-skin">{{ review.skin_type }}</span>
                  <span class="review-date">{{ review.review_date }}</span>
                </div>
                <p class="review-text">{{ review.text }}</p>
                <p class="review-recommend">👍 도움돼요 {{ review.recommend_count }}</p>
              </div>
            </div>
          </section>
        </div>
      </div>
    </div>
  </Transition>
</template>

<style scoped>
.overlay {
  position: fixed;
  inset: 0;
  background: rgba(0, 0, 0, 0.4);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 200;
  padding: 24px;
}

.modal {
  background: var(--surface);
  border-radius: 18px;
  width: 100%;
  max-width: 560px;
  max-height: 85vh;
  overflow-y: auto;
  position: relative;
}

.close-btn {
  position: absolute;
  top: 14px;
  right: 16px;
  width: 32px;
  height: 32px;
  border: none;
  background: rgba(0,0,0,0.04);
  border-radius: 50%;
  font-size: 20px;
  color: var(--text-secondary);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1;
}
.close-btn:hover { background: rgba(0,0,0,0.08); }

.head {
  display: flex;
  gap: 18px;
  padding: 28px;
  border-bottom: 1px solid var(--border);
}

.image {
  width: 120px;
  height: 120px;
  border-radius: 12px;
  background: var(--surface-hover);
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}
.img-placeholder { font-size: 52px; }

.head-info { flex: 1; min-width: 0; display: flex; flex-direction: column; gap: 6px; }
.brand { font-size: 13px; color: var(--text-muted); }
.name { font-size: 19px; font-weight: 700; line-height: 1.35; }

.rating-row { display: flex; align-items: center; gap: 6px; margin-top: 2px; }
.stars { color: #F5A623; font-size: 14px; letter-spacing: -1px; }
.rating-num { font-size: 14px; font-weight: 600; }
.review-count { font-size: 12px; color: var(--text-muted); }

.price { font-size: 18px; font-weight: 700; margin-top: 4px; }

.head-actions { display: flex; gap: 8px; margin-top: 10px; }
.like-btn {
  padding: 9px 16px;
  border: 1px solid var(--border);
  border-radius: 8px;
  background: var(--surface);
  font-size: 13px;
  cursor: pointer;
  transition: all 0.15s;
}
.like-btn:hover { background: var(--bg); }
.like-btn.liked { color: #E53935; border-color: #FECACA; background: #FFF5F5; }

.oliveyoung-btn {
  padding: 9px 16px;
  border: none;
  border-radius: 8px;
  background: var(--text-primary);
  color: #fff;
  font-size: 13px;
  font-weight: 500;
  display: flex;
  align-items: center;
}

.body { padding: 24px 28px 28px; display: flex; flex-direction: column; gap: 24px; }

.section { display: flex; flex-direction: column; gap: 12px; }
.section-title { font-size: 15px; font-weight: 700; }

.ai-section .ai-summary {
  background: linear-gradient(135deg, #F3EEFB 0%, #EDF3FB 100%);
  border-radius: 12px;
  padding: 16px;
  font-size: 13px;
  line-height: 1.7;
  color: #3A3A4A;
}

.satisfaction-list { display: flex; flex-direction: column; gap: 10px; }
.satisfaction-row { display: flex; align-items: center; gap: 12px; }
.sat-type { font-size: 13px; width: 48px; flex-shrink: 0; }
.sat-bar { flex: 1; height: 8px; background: var(--bg); border-radius: 4px; overflow: hidden; }
.sat-fill { height: 100%; background: var(--ai-avatar); border-radius: 4px; }
.sat-value { font-size: 12px; color: var(--text-secondary); width: 38px; text-align: right; flex-shrink: 0; }

.review-list { display: flex; flex-direction: column; gap: 10px; }
.review-card {
  background: var(--bg);
  border-radius: 10px;
  padding: 14px;
  display: flex;
  flex-direction: column;
  gap: 6px;
}
.review-head { display: flex; align-items: center; gap: 8px; flex-wrap: wrap; }
.review-stars { color: #F5A623; font-size: 12px; }
.review-user { font-size: 12px; font-weight: 600; }
.review-skin {
  font-size: 11px;
  background: var(--tag-bg);
  border-radius: 10px;
  padding: 1px 8px;
  color: var(--text-secondary);
}
.review-date { font-size: 11px; color: var(--text-muted); margin-left: auto; }
.review-text { font-size: 13px; line-height: 1.6; }
.review-recommend { font-size: 11px; color: var(--text-muted); }

/* Transition */
.modal-enter-active, .modal-leave-active { transition: opacity 0.2s; }
.modal-enter-from, .modal-leave-to { opacity: 0; }
.modal-enter-active .modal, .modal-leave-active .modal { transition: transform 0.2s; }
.modal-enter-from .modal, .modal-leave-to .modal { transform: scale(0.96); }
</style>
