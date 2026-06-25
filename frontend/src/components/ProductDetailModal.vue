<script setup>
import { computed, ref, watch, onUnmounted } from 'vue'
import { useRouter } from 'vue-router'
import { useProductDetailStore } from '@/stores/productDetail'
import { useLikesStore } from '@/stores/likes'
import { api } from '@/services/api'
import Icon from '@/components/Icon.vue'

const store = useProductDetailStore()
const likes = useLikesStore()
const router = useRouter()

// Esc로 닫기 + 열려있는 동안 배경 스크롤 잠금
function onKey(e) {
  if (e.key === 'Escape') store.close()
}
watch(() => store.isOpen, (open) => {
  if (open) {
    document.body.style.overflow = 'hidden'
    window.addEventListener('keydown', onKey)
  } else {
    document.body.style.overflow = ''
    window.removeEventListener('keydown', onKey)
  }
})
onUnmounted(() => {
  document.body.style.overflow = ''
  window.removeEventListener('keydown', onKey)
})

const product = computed(() => store.product)
const detail = computed(() => store.detail)

// ── 이 제품 관련 커뮤니티 글 ──
// 챗봇 추천의 목업 제품(비 UUID)은 서버에 글이 없으니 호출하지 않는다.
const UUID_RE = /^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/i
const relatedPosts = ref([])

async function fetchRelated(id) {
  relatedPosts.value = []
  if (!id || !UUID_RE.test(id)) return
  try {
    const { data } = await api.get(`/products/${id}/posts/`)
    relatedPosts.value = data?.results || (Array.isArray(data) ? data : [])
  } catch {
    relatedPosts.value = []
  }
}

watch(
  () => (store.isOpen ? store.product?.id : null),
  (id) => { if (id) fetchRelated(id) },
  { immediate: true },
)

function openPost(id) {
  store.close()
  router.push(`/community/${id}`)
}

const satisfactionList = computed(() => {
  if (!detail.value?.satisfaction_by_type) return []
  return Object.entries(detail.value.satisfaction_by_type)
    .map(([type, raw]) => {
      if (typeof raw === 'number') return { type, label: '', value: raw }
      // "아주 만족해요: 70%" 형태 파싱
      const m = String(raw).match(/^(.*?):\s*(\d+(?:\.\d+)?)%?$/)
      if (m) return { type, label: m[1].trim(), value: Number(m[2]) }
      const n = parseFloat(String(raw))
      return { type, label: '', value: isNaN(n) ? 0 : n }
    })
    .filter((item) => item.value > 0)
    .sort((a, b) => b.value - a.value)
})

function formatPrice(n) {
  return n != null ? n.toLocaleString('ko-KR') + '원' : '가격 정보 없음'
}

function stars(rating) {
  const r = Math.min(5, Math.max(0, Number(rating) || 0))
  const full = Math.floor(r)
  const half = r - full >= 0.5
  return '★'.repeat(full) + (half ? '½' : '') + '☆'.repeat(5 - full - (half ? 1 : 0))
}
</script>

<template>
  <!-- body로 Teleport: #app > * { position:relative } 규칙이 fixed 오버레이를 덮어쓰지 않게 -->
  <Teleport to="body">
  <Transition name="modal">
    <div v-if="store.isOpen" class="overlay" @click="store.close()">
      <div class="sheet" @click.stop>
        <div class="grab" />
        <button class="close-btn" @click="store.close()">×</button>

        <!-- 상단: 이미지 + 기본 정보 -->
        <div class="head">
          <div class="image">
            <img v-if="product?.image" :src="product.image" :alt="product?.name" class="detail-img" />
            <div v-else class="img-placeholder"><Icon name="leaf" :size="44" /></div>
          </div>
          <div class="head-info">
            <p class="brand">{{ product?.brand }}</p>
            <h2 class="name serif">{{ product?.name }}</h2>
            <div class="rating-row" v-if="detail">
              <span class="stars">{{ stars(detail.average_rating) }}</span>
              <span class="rating-num">{{ Number(detail.average_rating).toFixed(1) }}</span>
              <span class="review-count">리뷰 {{ detail.review_count.toLocaleString('ko-KR') }}개</span>
            </div>
            <p class="price serif">{{ formatPrice(product?.price) }}</p>
            <div class="head-actions">
              <button
                class="like-btn"
                :class="{ liked: likes.isLiked(product?.id) }"
                @click="likes.toggleLike(product)"
              ><Icon :name="likes.isLiked(product?.id) ? 'heart-fill' : 'heart'" :size="15" />{{ likes.isLiked(product?.id) ? ' 찜함' : ' 찜하기' }}</button>
              <a
                v-if="product?.oliveyoungUrl && product.oliveyoungUrl !== '#'"
                :href="product.oliveyoungUrl" target="_blank" rel="noopener noreferrer" class="oliveyoung-btn"
              >올리브영에서 보기 <Icon name="external" :size="14" /></a>
            </div>
          </div>
        </div>

        <div class="body" v-if="detail">
          <!-- 추천 이유 (추천/히스토리 카드에서 열었을 때만) -->
          <section v-if="product?.reason" class="section reason-section">
            <h3 class="section-title serif"><Icon name="sparkle" :size="16" /> 추천 이유</h3>
            <p class="reason-text">{{ product.reason }}</p>
          </section>

          <!-- AI 요약 -->
          <section class="section ai-section">
            <h3 class="section-title serif"><Icon name="sparkle" :size="16" /> AI 리뷰 요약</h3>
            <p class="ai-summary">{{ detail.ai_summary }}</p>
          </section>

          <!-- 피부 타입별 만족도 -->
          <section class="section">
            <h3 class="section-title serif">피부 타입별 만족도</h3>
            <div class="satisfaction-list">
              <div v-for="item in satisfactionList" :key="item.type" class="satisfaction-row">
                <span class="sat-type">{{ item.type }}</span>
                <div class="sat-bar"><div class="sat-fill" :style="{ width: item.value + '%' }" /></div>
                <span class="sat-value">{{ item.label ? item.label + ': ' + item.value + '%' : item.value + '%' }}</span>
              </div>
            </div>
          </section>

          <!-- 이 제품 관련 커뮤니티 글 -->
          <section v-if="relatedPosts.length" class="section">
            <h3 class="section-title serif"><Icon name="tag" :size="16" /> 이 제품 관련 글 {{ relatedPosts.length }}개</h3>
            <ul class="related-list">
              <li v-for="post in relatedPosts" :key="post.id" class="related-item" @click="openPost(post.id)">
                <div class="ri-top">
                  <span class="ri-cat">{{ post.category_label }}</span>
                  <span class="ri-stats">💬 {{ post.comment_count }} · ♥ {{ post.like_count }}</span>
                </div>
                <p class="ri-title">{{ post.title }}</p>
                <p class="ri-author">{{ post.author }}</p>
              </li>
            </ul>
          </section>
        </div>
      </div>
    </div>
  </Transition>
  </Teleport>
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
  padding: 26px 24px 24px;
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
  box-shadow: var(--sh-soft);
  border: 1px solid var(--line);
  overflow: hidden;
  transition: box-shadow var(--t) var(--ease);
}
.image:hover { box-shadow: var(--sh-hover); }
.detail-img { width: 100%; height: 100%; object-fit: cover; }
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
  display: flex;
  align-items: center;
  gap: 5px;
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
.section-title { display: flex; align-items: center; gap: 7px; font-size: 16px; font-weight: 600; color: var(--ink); }
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
.sat-value { font-size: 12px; color: var(--ink-soft); width: 90px; text-align: right; flex-shrink: 0; }

/* 관련 글 */
.related-list { display: flex; flex-direction: column; gap: 10px; }
.related-item {
  background: var(--sheet); border: 1px solid var(--line-soft); border-radius: var(--radius);
  padding: 12px 14px; cursor: pointer; box-shadow: var(--sh-soft);
  transition: transform var(--t-fast) var(--ease), box-shadow var(--t-fast) var(--ease);
}
.related-item:hover { transform: translateY(-2px); box-shadow: var(--sh-hover); }
.ri-top { display: flex; align-items: center; justify-content: space-between; margin-bottom: 6px; }
.ri-cat { font-size: 10.5px; font-weight: 700; padding: 3px 9px; border-radius: 99px; background: var(--sage-soft); color: var(--sage-ink); }
.ri-stats { font-size: 11.5px; color: var(--ink-faint); }
.ri-title { font-size: 14px; font-weight: 600; line-height: 1.35; color: var(--ink); }
.ri-author { font-size: 11.5px; color: var(--ink-faint); margin-top: 4px; }

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
