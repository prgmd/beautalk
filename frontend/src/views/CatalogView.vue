<script setup>
import { ref, computed, watch, onMounted } from 'vue'
import { api } from '@/services/api'
import { useLikesStore } from '@/stores/likes'
import { useProductDetailStore } from '@/stores/productDetail'
import { normalizeProduct } from '@/utils/product'
import GlobalSidebar from '@/components/GlobalSidebar.vue'
import Icon from '@/components/Icon.vue'

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
  return n != null ? n.toLocaleString('ko-KR') + '원' : '가격 정보 없음'
}
</script>

<template>
  <div class="screen">
    <div class="main">
      <header class="appbar">
        <h1 class="title t-page">둘러보기</h1>
      </header>

      <!-- 검색 -->
      <div class="searchbar">
        <Icon name="search" :size="18" class="s-ic" />
        <input v-model="search" type="search" enterkeyhint="search" aria-label="제품·브랜드 검색" placeholder="제품·브랜드 검색" />
        <button v-if="search" class="s-clear" @click="search = ''" aria-label="검색어 지우기"><Icon name="x" :size="15" /></button>
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

        <!-- 스켈레톤 -->
        <div v-if="loading" class="grid" aria-hidden="true">
          <div v-for="n in 8" :key="n" class="card skel">
            <div class="arch sk" />
            <div class="meta">
              <div class="sk-line sk" style="width:40%" />
              <div class="sk-line sk" style="width:80%" />
              <div class="sk-line sk" style="width:50%" />
            </div>
          </div>
        </div>

        <div v-if="!loading && pageItems.length" class="grid">
          <article v-for="(product, i) in pageItems" :key="product.id" class="card" :style="{ '--d': i * 35 + 'ms' }">
            <div class="arch" @click="productDetail.open(product)">
              <img v-if="product.image" :src="product.image" :alt="product.name" />
              <Icon v-else name="leaf" :size="38" class="ph" />
              <button
                class="heart"
                :class="{ liked: likes.isLiked(product.id) }"
                :aria-label="likes.isLiked(product.id) ? '찜 해제' : '찜하기'"
                :aria-pressed="likes.isLiked(product.id)"
                @click.stop="likes.toggleLike(product)"
              ><Icon :name="likes.isLiked(product.id) ? 'heart-fill' : 'heart'" :size="16" /></button>
            </div>
            <div
              class="meta" role="button" tabindex="0"
              @click="productDetail.open(product)"
              @keydown.enter.prevent="productDetail.open(product)"
              @keydown.space.prevent="productDetail.open(product)"
            >
              <p class="brand">{{ product.brand }}</p>
              <p class="name">{{ product.name }}</p>
              <p class="price serif">{{ formatPrice(product.price) }}</p>
            </div>
          </article>
        </div>

        <div v-if="isEmpty" class="empty">
          <span class="empty-art"><Icon name="leaf" :size="40" /></span>
          <template v-if="search || activeCategory">
            <p class="empty-text">조건에 맞는 제품이 없어요.</p>
            <button class="empty-cta" @click="search = ''; selectCategory('')">검색·필터 초기화</button>
          </template>
          <p v-else class="empty-text">표시할 제품이 없어요.</p>
        </div>

        <!-- 숫자 페이지네이션 -->
        <div v-if="!loading && pageCount > 1" class="pager">
          <button class="pg arrow" :disabled="page === 1" @click="goPage(page - 1)" aria-label="이전"><Icon name="chevron-left" :size="17" /></button>
          <button
            v-for="(p, i) in pages"
            :key="i"
            class="pg"
            :class="{ on: p === page, gap: p === '…' }"
            :disabled="p === '…'"
            @click="goPage(p)"
          >{{ p }}</button>
          <button class="pg arrow" :disabled="page === pageCount" @click="goPage(page + 1)" aria-label="다음"><Icon name="chevron-right" :size="17" /></button>
        </div>
      </div>
    </div>

    <GlobalSidebar />
  </div>
</template>

<style scoped>
.screen { height: 100%; display: flex; flex-direction: column; overflow: hidden; }
.main { flex: 1; min-height: 0; display: flex; flex-direction: column; overflow: hidden; }

.appbar { flex-shrink: 0; padding: calc(16px + env(safe-area-inset-top)) 20px 4px; }

.searchbar {
  flex-shrink: 0; display: flex; align-items: center; gap: 9px;
  margin: 16px 20px 0; padding: 12px 15px; border-radius: 99px;
  background: var(--card); border: 1px solid var(--line); box-shadow: var(--sh-sm);
  transition: border-color var(--t-fast), box-shadow var(--t-fast);
}
.searchbar:focus-within { border-color: var(--sage); box-shadow: 0 0 0 3px rgba(126,139,109,.15); }
.s-ic { color: var(--ink-faint); }
.searchbar input { flex: 1; border: none; background: none; outline: none; font-size: 14px; color: var(--ink); font-family: inherit; }
.searchbar input::placeholder { color: var(--ink-faint); }
.s-clear { width: 24px; height: 24px; border-radius: 50%; background: var(--panel); color: var(--ink-soft); display: flex; align-items: center; justify-content: center; flex-shrink: 0; }
.s-clear:hover { background: var(--line); color: var(--ink); }

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

.body { flex: 1; min-height: 0; overflow-y: auto; padding: 14px 20px 24px; }
.msg { font-size: 13px; color: var(--ink-soft); padding: 16px 2px; text-align: center; }
.msg.err { color: var(--danger); }

.grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(155px, 1fr)); gap: 16px; }
.card {
  background: var(--card); border: 1px solid var(--line-soft); border-radius: var(--radius-lg);
  padding: 10px; box-shadow: var(--sh-soft);
  animation: card-in .5s var(--ease) both; animation-delay: var(--d, 0ms);
  transition: transform var(--t) var(--ease), box-shadow var(--t) var(--ease);
}
.card:hover { transform: translateY(-4px); box-shadow: var(--sh-hover); }
.arch {
  position: relative; aspect-ratio: 1; border-radius: 80px 80px 14px 14px; overflow: hidden;
  background: linear-gradient(170deg,#F1EADE,#E7E3D2 60%,#DFE7DF); cursor: pointer;
  display: flex; align-items: center; justify-content: center;
}
.arch img { width: 100%; height: 100%; object-fit: cover; transition: transform .6s var(--ease); }
.card:hover .arch img { transform: scale(1.06); }
.ph { color: var(--sage); opacity: .5; }
.heart {
  position: absolute; top: 10px; right: 10px; width: 33px; height: 33px; border-radius: 50%;
  background: rgba(28,22,16,.4); border: 1px solid rgba(255,255,255,.35);
  box-shadow: 0 2px 8px rgba(0,0,0,.28); backdrop-filter: blur(3px);
  -webkit-backdrop-filter: blur(3px); color: #fff;
  display: flex; align-items: center; justify-content: center;
  transition: transform var(--t-fast) var(--ease-back), background var(--t-fast);
}
.heart:active { transform: scale(.88); }
.heart.liked { background: var(--rose); border-color: transparent; color: #fff; }
.meta { padding: 13px 6px 5px; cursor: pointer; }
.brand { font-size: 10px; letter-spacing: 1.4px; text-transform: uppercase; color: var(--ink-faint); }
.name { font-size: 13.5px; font-weight: 600; line-height: 1.4; margin: 5px 0 8px; color: var(--ink); }
.card:hover .name { text-decoration: underline; text-underline-offset: 2px; text-decoration-thickness: 1px; }
.price { font-size: 16px; color: var(--ink); }

/* 스켈레톤 */
.skel { pointer-events: none; animation: none; }
.sk { position: relative; overflow: hidden; background: var(--panel); }
.sk::after {
  content: ''; position: absolute; inset: 0;
  background: linear-gradient(100deg, transparent 20%, rgba(255,255,255,.65) 50%, transparent 80%);
  transform: translateX(-100%); animation: shimmer 1.3s infinite;
}
.sk-line { height: 11px; border-radius: 6px; margin: 8px 0; }

.empty { display: flex; flex-direction: column; align-items: center; gap: 12px; padding: 60px 0; text-align: center; }
.empty-art {
  width: 72px; height: 72px; border-radius: 50%; display: flex; align-items: center; justify-content: center;
  background: var(--sage-soft); color: var(--sage-ink);
}
.empty-text { font-size: 14px; color: var(--ink-soft); }
.empty-cta {
  margin-top: 4px; padding: 9px 18px; border-radius: 99px; font-size: 13px; font-weight: 600;
  color: var(--ink); background: var(--card); border: 1px solid var(--line); box-shadow: var(--sh-sm);
}

/* 숫자 페이지네이션 */
.pager { display: flex; align-items: center; justify-content: center; gap: 6px; margin: 26px auto 8px; flex-wrap: wrap; }
.pg {
  min-width: 36px; height: 36px; padding: 0 8px; border-radius: 10px;
  border: 1px solid var(--line); background: var(--sheet); font-size: 13px; font-weight: 600; color: var(--ink-soft);
  display: inline-flex; align-items: center; justify-content: center; transition: all var(--t-fast);
}
.pg:hover:not(:disabled):not(.on) { background: var(--card); color: var(--ink); }
.pg.on { background: var(--ink); color: var(--canvas); border-color: var(--ink); box-shadow: var(--sh-sm); }
.pg.arrow { padding: 0 6px; }
.pg.gap { border: none; background: none; min-width: 20px; color: var(--ink-faint); }
.pg:disabled { opacity: .4; cursor: default; }

@keyframes card-in { from { opacity: 0; transform: translateY(12px); } to { opacity: 1; transform: none; } }
@keyframes shimmer { 100% { transform: translateX(100%); } }
@media (prefers-reduced-motion: reduce) {
  .card { animation: none; }
  .sk::after { animation: none; }
  .card:hover .arch img { transform: none; }
}

/* ── 데스크탑(≥900px) ── */
@media (min-width: 900px) {
  .screen { flex-direction: row; }
  .appbar, .filters, .body, .searchbar { max-width: 1000px; width: 100%; margin-left: auto; margin-right: auto; }
  .appbar { padding: 40px 40px 6px; }
  .searchbar { margin-top: 18px; max-width: 1000px; }
  .filters { padding: 14px 40px 16px; }
  .body { padding: 12px 40px 40px; }
  .grid { grid-template-columns: repeat(auto-fill, minmax(195px, 1fr)); gap: 22px; }
}
</style>
