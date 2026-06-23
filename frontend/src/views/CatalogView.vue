<script setup>
import { ref, computed, onMounted } from 'vue'
import { api } from '@/services/api'
import { useLikesStore } from '@/stores/likes'
import { useProductDetailStore } from '@/stores/productDetail'
import { normalizeProduct } from '@/utils/product'
import GlobalSidebar from '@/components/GlobalSidebar.vue'

const likes = useLikesStore()
const productDetail = useProductDetailStore()

const products = ref([]) // 정규화된 product 목록(누적)
const page = ref(1)
const hasMore = ref(false)
const loading = ref(false)
const loadingMore = ref(false)
const errorMsg = ref('')
const activeCategory = ref('') // '' = 전체

// 불러온 제품에서 카테고리를 모아 필터 칩으로 제공한다(별도 카테고리 API가 없어서).
const categories = ref([])

function rememberCategories(items) {
  const set = new Set(categories.value)
  items.forEach((p) => { if (p.category) set.add(p.category) })
  categories.value = [...set]
}

// GET /products/ (페이지네이션: { count, next, previous, results })
async function fetchPage(reset = false) {
  if (reset) {
    page.value = 1
    products.value = []
    loading.value = true
  } else {
    loadingMore.value = true
  }
  errorMsg.value = ''
  try {
    const params = new URLSearchParams({ page: String(page.value) })
    if (activeCategory.value) params.set('category', activeCategory.value)
    const { data } = await api.get(`/products/?${params.toString()}`)
    const results = (data?.results || []).map(normalizeProduct)
    products.value = reset ? results : [...products.value, ...results]
    hasMore.value = !!data?.next
    rememberCategories(results)
  } catch {
    errorMsg.value = '제품을 불러오지 못했어요. 잠시 후 다시 시도해 주세요.'
  } finally {
    loading.value = false
    loadingMore.value = false
  }
}

function loadMore() {
  if (loadingMore.value || !hasMore.value) return
  page.value += 1
  fetchPage(false)
}

function selectCategory(cat) {
  if (activeCategory.value === cat) return
  activeCategory.value = cat
  fetchPage(true)
}

const isEmpty = computed(() => !loading.value && products.value.length === 0)

onMounted(() => fetchPage(true))

function formatPrice(n) {
  return n?.toLocaleString('ko-KR') + '원'
}
</script>

<template>
  <div class="screen">
    <div class="main">
      <header class="appbar">
        <div>
          <span class="eyebrow">browse</span>
          <h1 class="title serif">둘러보기</h1>
        </div>
      </header>

      <!-- 카테고리 필터 -->
      <nav v-if="categories.length" class="filters">
        <button class="chip" :class="{ on: activeCategory === '' }" @click="selectCategory('')">전체</button>
        <button
          v-for="cat in categories"
          :key="cat"
          class="chip"
          :class="{ on: activeCategory === cat }"
          @click="selectCategory(cat)"
        >{{ cat }}</button>
      </nav>

      <div class="body">
        <p v-if="errorMsg" class="msg err">{{ errorMsg }}</p>
        <p v-if="loading" class="msg">제품을 불러오는 중...</p>

        <div v-if="products.length" class="grid">
          <article v-for="product in products" :key="product.id" class="card">
            <div class="arch" @click="productDetail.open(product)">
              <img v-if="product.image" :src="product.image" :alt="product.name" />
              <span v-else class="ph">🧴</span>
              <button
                class="heart"
                :class="{ liked: likes.isLiked(product.id) }"
                @click.stop="likes.toggleLike(product)"
              >{{ likes.isLiked(product.id) ? '♥' : '♡' }}</button>
            </div>
            <div class="meta" @click="productDetail.open(product)">
              <p class="brand">{{ product.brand }}</p>
              <p class="name">{{ product.name }}</p>
              <p class="price serif">{{ formatPrice(product.price) }}</p>
            </div>
          </article>
        </div>

        <div v-if="isEmpty" class="empty">
          <p class="empty-icon">🌿</p>
          <p class="empty-text">표시할 제품이 없어요.</p>
        </div>

        <button v-if="hasMore && !loading" class="more-btn" :disabled="loadingMore" @click="loadMore">
          {{ loadingMore ? '불러오는 중...' : '더 보기' }}
        </button>
      </div>
    </div>

    <GlobalSidebar />
  </div>
</template>

<style scoped>
.screen { height: 100%; display: flex; flex-direction: column; overflow: hidden; }
.main { flex: 1; min-height: 0; display: flex; flex-direction: column; overflow: hidden; }

.appbar { flex-shrink: 0; padding: calc(12px + env(safe-area-inset-top)) 20px 6px; }
.eyebrow { font-size: 10px; letter-spacing: 4px; text-transform: uppercase; color: var(--sage); }
.title { font-size: 26px; font-weight: 500; letter-spacing: -.3px; margin-top: 4px; }

.filters {
  flex-shrink: 0; display: flex; gap: 8px; overflow-x: auto;
  padding: 10px 20px 12px; -ms-overflow-style: none; scrollbar-width: none;
}
.filters::-webkit-scrollbar { display: none; }
.chip {
  flex-shrink: 0; padding: 8px 15px; border-radius: 99px; font-size: 13px; font-weight: 600;
  color: var(--ink-soft); background: var(--sheet); border: 1px solid var(--line); transition: all var(--t-fast);
}
.chip:active { transform: scale(.97); }
.chip.on { background: var(--ink); color: var(--canvas); border-color: var(--ink); box-shadow: var(--sh-sm); }

.body { flex: 1; min-height: 0; overflow-y: auto; padding: 6px 20px 24px; }
.msg { font-size: 13px; color: var(--ink-soft); padding: 16px 2px; text-align: center; }
.msg.err { color: var(--danger); }

.grid { display: grid; grid-template-columns: 1fr 1fr; gap: 14px; }
.card {
  background: var(--card); border: 1px solid var(--line-soft); border-radius: var(--radius-lg);
  padding: 10px; box-shadow: var(--sh-sm); animation: bt-rise .4s var(--ease) both;
  transition: transform var(--t) var(--ease), box-shadow var(--t) var(--ease);
}
.card:hover { transform: translateY(-3px); box-shadow: var(--sh-md); }
.arch {
  position: relative; aspect-ratio: 1; border-radius: 80px 80px 12px 12px; overflow: hidden;
  background: linear-gradient(170deg,#EFE7DB,#E6E3D0 60%,#DEE7DF); cursor: pointer;
  display: flex; align-items: center; justify-content: center;
}
.arch::before {
  content: ''; position: absolute; left: 0; right: 0; bottom: 0; height: 44%;
  background: repeating-linear-gradient(180deg, transparent 0 8px, rgba(34,42,46,.05) 8px 9px);
}
.arch img { width: 100%; height: 100%; object-fit: cover; }
.ph { font-size: 36px; position: relative; }
.heart {
  position: absolute; top: 9px; right: 9px; width: 30px; height: 30px; border-radius: 50%;
  background: rgba(255,255,255,.9); box-shadow: var(--sh-sm); font-size: 13px; color: var(--rose);
  display: flex; align-items: center; justify-content: center;
}
.heart.liked { background: var(--rose); color: #fff; }
.meta { padding: 11px 6px 4px; cursor: pointer; }
.brand { font-size: 10.5px; letter-spacing: 1.2px; text-transform: uppercase; color: var(--ink-faint); }
.name { font-size: 13.5px; font-weight: 600; line-height: 1.35; margin: 4px 0 6px; }
.price { font-size: 15px; }

.empty { display: flex; flex-direction: column; align-items: center; gap: 8px; padding: 56px 0; text-align: center; }
.empty-icon { font-size: 38px; }
.empty-text { font-size: 14px; color: var(--ink-soft); }

.more-btn {
  display: block; margin: 22px auto 8px; padding: 12px 26px; border-radius: 99px;
  border: 1px solid var(--line); background: var(--sheet); font-size: 14px; font-weight: 600; box-shadow: var(--sh-sm);
}
.more-btn:disabled { opacity: .6; }

/* ── 데스크탑(≥900px) ── */
@media (min-width: 900px) {
  .screen { flex-direction: row; }
  .appbar, .filters, .body { max-width: 980px; width: 100%; margin: 0 auto; }
  .appbar { padding: 28px 40px 6px; }
  .filters { padding: 10px 40px 14px; }
  .body { padding: 6px 40px 32px; }
  .title { font-size: 30px; }
  .grid { grid-template-columns: repeat(4, 1fr); gap: 18px; }
}
</style>
