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
  const r = Math.min(5, Math.max(0, Number(rating) || 0))
  const full = Math.floor(r)
  const half = r - full >= 0.5
  return '★'.repeat(full) + (half ? '½' : '') + '☆'.repeat(5 - full - (half ? 1 : 0))
}
</script>

<template>
  <Transition name="modal">
    <div v-if="store.isOpen" class="overlay" @click="store.close()">
      <div class="sheet" @click.stop>
        <div class="grab" />
        <button class="close-btn" @click="store.close()">×</button>

        <!-- 상단: 이미지 + 기본 정보 -->
        <div class="head">
          <div class="image">
            <div class="img-placeholder">🧴</div>
          </div>
          <div class="head-info">
            <p class="brand">{{ product?.brand }}</p>
            <h2 class="name serif">{{ product?.name }}</h2>
            <div class="rating-row" v-if="detail">
              <span class="stars">{{ stars(detail.average_rating) }}</span>
              <span class="rating-num">{{ detail.average_rating }}</span>
              <span class="review-count">리뷰 {{ detail.review_count.toLocaleString('ko-KR') }}개</span>
            </div>
            <p class="price serif">{{ formatPrice(product?.price) }}</p>
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
          <!-- 추천 이유 (추천/히스토리 카드에서 열었을 때만) -->
          <section v-if="product?.reason" class="section reason-section">
            <h3 class="section-title serif">💡 추천 이유</h3>
            <p class="reason-text">{{ product.reason }}</p>
          </section>

          <!-- AI 요약 -->
          <section class="section ai-section">
            <h3 class="section-title serif">✨ AI 리뷰 요약</h3>
            <p class="ai-summary">{{ detail.ai_summary }}</p>
          </section>

          <!-- 피부 타입별 만족도 -->
          <section class="section">
            <h3 class="section-title serif">피부 타입별 만족도</h3>
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
            <h3 class="section-title serif">실제 리뷰</h3>
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
  z-index: 200;
  background: rgba(34, 28, 22, 0.42);
  backdrop-filter: blur(6px);
  -webkit-backdrop-filter: blur(6px);
  display: flex;
  align-items: flex-end;
  justify-content: center;
}

.sheet {
  position: relative;
  width: 100%;
  max-width: 480px;
  margin: 0 auto;
  background: var(--card);
  border-radius: 26px 26px 0 0;
  box-shadow: var(--sh-lg);
  max-height: 90vh;
  overflow-y: auto;
  padding-bottom: calc(20px + env(safe-area-inset-bottom));
}

.grab {
  position: sticky;
  top: 0;
  z-index: 2;
  width: 36px;
  height: 4px;
  margin: 12px auto 4px;
  border-radius: 999px;
  background: var(--line-strong);
}

.close-btn {
  position: absolute;
  top: 14px;
  right: 16px;
  width: 32px;
  height: 32px;
  border-radius: 50%;
  background: var(--panel);
  font-size: 20px;
  color: var(--ink-soft);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 3;
  transition: background var(--t-fast) var(--ease);
}
.close-btn:hover { background: var(--line); }

.head {
  display: flex;
  gap: 18px;
  padding: 8px 24px 24px;
  border-bottom: 1px solid var(--line-soft);
}

/* ARCH treatment for image */
.image {
  width: 116px;
  height: 140px;
  border-radius: 58px 58px var(--radius) var(--radius);
  background: var(--sage-soft);
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
  box-shadow: var(--sh-sm);
  border: 1px solid var(--line);
}
.img-placeholder { font-size: 52px; }

.head-info { flex: 1; min-width: 0; display: flex; flex-direction: column; gap: 6px; }
.brand { font-size: 12px; letter-spacing: 0.04em; text-transform: uppercase; color: var(--ink-faint); }
.name { font-size: 21px; font-weight: 600; line-height: 1.3; color: var(--ink); }

.rating-row { display: flex; align-items: center; gap: 6px; margin-top: 2px; }
.stars { color: var(--rose); font-size: 14px; letter-spacing: -1px; }
.rating-num { font-size: 14px; font-weight: 600; color: var(--ink); }
.review-count { font-size: 12px; color: var(--ink-faint); }

.price { font-size: 20px; font-weight: 600; margin-top: 4px; color: var(--ink); }

.head-actions { display: flex; gap: 8px; margin-top: 12px; }
.like-btn {
  padding: 10px 16px;
  border: 1px solid var(--rose-soft);
  border-radius: var(--radius-sm);
  background: var(--card);
  color: var(--rose-ink);
  font-size: 13px;
  font-weight: 600;
  cursor: pointer;
  transition: all var(--t-fast) var(--ease);
}
.like-btn:hover { border-color: var(--rose); }
.like-btn.liked { color: var(--card); border-color: transparent; background: var(--rose); }

.oliveyoung-btn {
  padding: 10px 16px;
  border-radius: var(--radius-sm);
  background: var(--ink);
  color: var(--canvas);
  font-size: 13px;
  font-weight: 600;
  display: flex;
  align-items: center;
  box-shadow: var(--sh-ink);
  transition: transform var(--t-fast) var(--ease);
}
.oliveyoung-btn:hover { transform: translateY(-1px); }

.body { padding: 24px; display: flex; flex-direction: column; gap: 26px; }

.section { display: flex; flex-direction: column; gap: 12px; }
.section-title { font-size: 16px; font-weight: 600; color: var(--ink); }

.ai-section .ai-summary {
  background: var(--sage-soft);
  border: 1px solid var(--line);
  border-radius: var(--radius);
  padding: 16px;
  font-size: 13px;
  line-height: 1.75;
  color: var(--sage-ink);
}

.reason-section .reason-text {
  background: var(--panel);
  border: 1px solid var(--line);
  border-left: 3px solid var(--sage);
  border-radius: var(--radius);
  padding: 14px 16px;
  font-size: 13px;
  line-height: 1.75;
  color: var(--ink-soft);
}

.satisfaction-list { display: flex; flex-direction: column; gap: 12px; }
.satisfaction-row { display: flex; align-items: center; gap: 12px; }
.sat-type { font-size: 13px; width: 48px; flex-shrink: 0; color: var(--ink-soft); }
.sat-bar { flex: 1; height: 8px; background: var(--panel); border-radius: 999px; overflow: hidden; }
.sat-fill {
  height: 100%;
  background: linear-gradient(90deg, var(--sage), var(--rose));
  border-radius: 999px;
  transition: width var(--t-slow) var(--ease);
}
.sat-value { font-size: 12px; color: var(--ink-soft); width: 38px; text-align: right; flex-shrink: 0; }

.review-list { display: flex; flex-direction: column; gap: 10px; }
.review-card {
  background: var(--sheet);
  border: 1px solid var(--line-soft);
  border-radius: var(--radius);
  padding: 14px 16px;
  display: flex;
  flex-direction: column;
  gap: 6px;
  box-shadow: var(--sh-sm);
}
.review-head { display: flex; align-items: center; gap: 8px; flex-wrap: wrap; }
.review-stars { color: var(--rose); font-size: 12px; }
.review-user { font-size: 12px; font-weight: 600; color: var(--ink); }
.review-skin {
  font-size: 11px;
  background: var(--sage-soft);
  border-radius: 999px;
  padding: 2px 9px;
  color: var(--sage-ink);
}
.review-date { font-size: 11px; color: var(--ink-faint); margin-left: auto; }
.review-text { font-size: 13px; line-height: 1.65; color: var(--ink); }
.review-recommend { font-size: 11px; color: var(--ink-faint); }

/* Transition — slide up from bottom */
.modal-enter-active, .modal-leave-active { transition: opacity var(--t) var(--ease); }
.modal-enter-from, .modal-leave-to { opacity: 0; }
.modal-enter-active .sheet, .modal-leave-active .sheet { transition: transform var(--t) var(--ease); }
.modal-enter-from .sheet, .modal-leave-to .sheet { transform: translateY(100%); }

/* Desktop — centered dialog */
@media (min-width: 900px) {
  .overlay { align-items: center; }
  .sheet {
    max-width: 520px;
    margin: 0 auto;
    border-radius: var(--radius-xl);
    max-height: 86vh;
    overflow-y: auto;
    box-shadow: var(--sh-lg);
    padding-bottom: 24px;
  }
  .grab { display: none; }
  .modal-enter-from .sheet, .modal-leave-to .sheet { transform: scale(0.96); }
}
</style>
