<script setup>
import { ref, computed, watch, onMounted } from 'vue'
import { api } from '@/services/api'
import { useLikesStore } from '@/stores/likes'
import { useProductDetailStore } from '@/stores/productDetail'
import { normalizeProduct } from '@/utils/product'
import GlobalSidebar from '@/components/GlobalSidebar.vue'

const likes = useLikesStore()
const productDetail = useProductDetailStore()

const all = ref([]) // 전체 제품(정규화)
const loading = ref(false)
const errorMsg = ref('')
const search = ref('')
const activeCategory = ref('') // '' = 전체
const page = ref(1)
const PAGE_SIZE = 12

const bodyEl = ref(null)

// 전체를 한 번에 받는다: 1페이지로 count 파악 → 나머지 페이지 병렬 조회 → 합침.
// (검색·카테고리·페이지네이션을 모두 클라이언트에서 처리해 동선이 깔끔해짐)
async function fetchAll() {
  loading.value = true
  errorMsg.value = ''
  try {
    const first = await api.get('/products/?page=1')
    const count = first.data?.count || 0
    let items = (first.data?.results || []).map(normalizeProduct)
    const per = first.data?.results?.length || 10
    const totalPages = per ? Math.ceil(count / per) : 1
    if (totalPages > 1) {
      const rest = await Promise.all(
        Array.from({ length: totalPages - 1 }, (_, i) => api.get(`/products/?page=${i + 2}`)),
      )
      rest.forEach((r) => { items = items.concat((r.data?.results || []).map(normalizeProduct)) })
    }
    // 시드에 같은 제품(브랜드+이름)이 중복 수집돼 있어 화면에선 1개만 보이도록 정리한다.
    const seen = new Set()
    all.value = items.filter((p) => {
      const k = `${p.brand}__${p.name}`
      if (seen.has(k)) return false
      seen.add(k)
      return true
    })
  } catch {
    errorMsg.value = '제품을 불러오지 못했어요. 잠시 후 다시 시도해 주세요.'
  } finally {
    loading.value = false
  }
}

const categories = computed(() => {
  const set = new Set()
  all.value.forEach((p) => { if (p.category) set.add(p.category) })
  return [...set]
})

const filtered = computed(() => {
  const q = search.value.trim().toLowerCase()
  return all.value.filter((p) => {
    if (activeCategory.value && p.category !== activeCategory.value) return false
    if (q && !`${p.name} ${p.brand}`.toLowerCase().includes(q)) return false
    return true
  })
})

const pageCount = computed(() => Math.max(1, Math.ceil(filtered.value.length / PAGE_SIZE)))
const pageItems = computed(() => filtered.value.slice((page.value - 1) * PAGE_SIZE, page.value * PAGE_SIZE))

// 표시할 페이지 번호(윈도우 + 생략)
const pages = computed(() => {
  const n = pageCount.value
  const c = page.value
  if (n <= 7) return Array.from({ length: n }, (_, i) => i + 1)
  const out = [1]
  const lo = Math.max(2, c - 1)
  const hi = Math.min(n - 1, c + 1)
  if (lo > 2) out.push('…')
  for (let i = lo; i <= hi; i++) out.push(i)
  if (hi < n - 1) out.push('…')
  out.push(n)
  return out
})

// 필터/검색 바뀌면 1페이지로
watch([activeCategory, search], () => { page.value = 1 })

function goPage(p) {
  if (p === '…' || p === page.value) return
  page.value = p
  if (bodyEl.value) bodyEl.value.scrollTop = 0
}
function selectCategory(cat) { activeCategory.value = cat }

const isEmpty = computed(() => !loading.value && filtered.value.length === 0)

onMounted(fetchAll)

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

      <!-- 검색 -->
      <div class="searchbar">
        <span class="s-ic">🔎</span>
        <input v-model="search" placeholder="제품·브랜드 검색" />
        <button v-if="search" class="s-clear" @click="search = ''" aria-label="검색어 지우기">×</button>
      </div>

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

      <div ref="bodyEl" class="body">
        <p v-if="errorMsg" class="msg err">{{ errorMsg }}</p>
        <p v-if="loading" class="msg">제품을 불러오는 중...</p>

        <div v-if="pageItems.length" class="grid">
          <article v-for="product in pageItems" :key="product.id" class="card">
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

        <!-- 숫자 페이지네이션 -->
        <div v-if="!loading && pageCount > 1" class="pager">
          <button class="pg arrow" :disabled="page === 1" @click="goPage(page - 1)" aria-label="이전">‹</button>
          <button
            v-for="(p, i) in pages"
            :key="i"
            class="pg"
            :class="{ on: p === page, gap: p === '…' }"
            :disabled="p === '…'"
            @click="goPage(p)"
          >{{ p }}</button>
          <button class="pg arrow" :disabled="page === pageCount" @click="goPage(page + 1)" aria-label="다음">›</button>
        </div>
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

.searchbar {
  flex-shrink: 0; display: flex; align-items: center; gap: 8px;
  margin: 6px 20px 0; padding: 11px 14px; border-radius: var(--radius);
  background: var(--card); border: 1px solid var(--line); box-shadow: var(--sh-sm);
  transition: border-color var(--t-fast), box-shadow var(--t-fast);
}
.searchbar:focus-within { border-color: var(--sage); box-shadow: 0 0 0 3px rgba(126,139,109,.15); }
.s-ic { font-size: 14px; opacity: .7; }
.searchbar input { flex: 1; border: none; background: none; outline: none; font-size: 14px; color: var(--ink); font-family: inherit; }
.searchbar input::placeholder { color: var(--ink-faint); }
.s-clear { width: 22px; height: 22px; border-radius: 50%; background: var(--panel); color: var(--ink-soft); font-size: 15px; flex-shrink: 0; }

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

.grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(150px, 1fr)); gap: 14px; }
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

/* 숫자 페이지네이션 */
.pager { display: flex; align-items: center; justify-content: center; gap: 6px; margin: 26px auto 8px; flex-wrap: wrap; }
.pg {
  min-width: 36px; height: 36px; padding: 0 8px; border-radius: 10px;
  border: 1px solid var(--line); background: var(--sheet); font-size: 13px; font-weight: 600; color: var(--ink-soft);
  display: inline-flex; align-items: center; justify-content: center; transition: all var(--t-fast);
}
.pg:hover:not(:disabled):not(.on) { background: var(--card); color: var(--ink); }
.pg.on { background: var(--ink); color: var(--canvas); border-color: var(--ink); box-shadow: var(--sh-sm); }
.pg.arrow { font-size: 16px; }
.pg.gap { border: none; background: none; min-width: 20px; color: var(--ink-faint); }
.pg:disabled { opacity: .4; cursor: default; }

/* ── 데스크탑(≥900px) ── */
@media (min-width: 900px) {
  .screen { flex-direction: row; }
  .appbar, .filters, .body, .searchbar { max-width: 980px; width: 100%; margin-left: auto; margin-right: auto; }
  .appbar { padding: 28px 40px 6px; }
  .searchbar { margin-top: 8px; max-width: 900px; }
  .filters { padding: 10px 40px 14px; }
  .body { padding: 6px 40px 32px; }
  .title { font-size: 30px; }
  .grid { grid-template-columns: repeat(auto-fill, minmax(185px, 1fr)); gap: 18px; }
}
</style>
