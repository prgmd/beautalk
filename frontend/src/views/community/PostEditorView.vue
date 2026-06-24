<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRoute, useRouter, onBeforeRouteLeave } from 'vue-router'
import { api } from '@/services/api'
import { useCommunityStore, CATEGORIES } from '@/stores/community'
import { useConfirmStore } from '@/stores/confirm'
import { normalizeProduct } from '@/utils/product'
import GlobalSidebar from '@/components/GlobalSidebar.vue'
import Icon from '@/components/Icon.vue'

const confirm = useConfirmStore()
const saved = ref(false)

const route = useRoute()
const router = useRouter()
const community = useCommunityStore()

const editId = computed(() => route.params.id || null)
const isEdit = computed(() => !!editId.value)

const category = ref('free')
const title = ref('')
const content = ref('')
const selectedProducts = ref([]) // [{ id, brand, name, image }] — 복수 태그

const saving = ref(false)
const error = ref('')
const loading = ref(false)

// ── 제품 태그 검색(선택) ──
const allProducts = ref([])
const productsLoaded = ref(false)
const productQuery = ref('')
const pickerOpen = ref(false)

const productResults = computed(() => {
  const q = productQuery.value.trim().toLowerCase()
  if (!q) return []
  const picked = new Set(selectedProducts.value.map((p) => p.id))
  return allProducts.value
    .filter((p) => !picked.has(p.id) && `${p.name} ${p.brand}`.toLowerCase().includes(q))
    .slice(0, 8)
})

// 전체 제품을 한 번 받아 클라이언트에서 검색(카탈로그와 동일 전략, 중복 정리 포함)
async function ensureProducts() {
  if (productsLoaded.value) return
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
    const seen = new Set()
    allProducts.value = items.filter((p) => {
      const k = `${p.brand}__${p.name}`
      if (seen.has(k)) return false
      seen.add(k)
      return true
    })
  } catch {
    /* 검색 불가 시 태그 없이 진행 가능 */
  } finally {
    productsLoaded.value = true
  }
}

function focusPicker() {
  pickerOpen.value = true
  ensureProducts()
}
function pickProduct(p) {
  if (!selectedProducts.value.some((s) => s.id === p.id)) selectedProducts.value.push(p)
  productQuery.value = ''
  // 계속 추가할 수 있도록 picker는 열어둔다
}
function removeProduct(id) {
  selectedProducts.value = selectedProducts.value.filter((p) => p.id !== id)
}

const canSubmit = computed(() => title.value.trim() && content.value.trim() && !saving.value)

async function submit() {
  if (!canSubmit.value) return
  saving.value = true
  error.value = ''
  const payload = {
    category: category.value,
    title: title.value.trim(),
    content: content.value.trim(),
    product_ids: selectedProducts.value.map((p) => p.id),
  }
  try {
    const data = isEdit.value
      ? await community.updatePost(editId.value, payload)
      : await community.createPost(payload)
    saved.value = true
    router.replace(`/community/${data.id}`)
  } catch (e) {
    error.value = e?.data?.detail || '저장에 실패했어요. 입력을 확인해 주세요.'
    saving.value = false
  }
}

function cancel() {
  if (isEdit.value) router.push(`/community/${editId.value}`)
  else router.push('/community')
}

async function loadForEdit() {
  loading.value = true
  try {
    const data = await community.fetchPost(editId.value)
    category.value = data.category
    title.value = data.title
    content.value = data.content
    selectedProducts.value = (data.products || []).map(normalizeProduct)
  } catch {
    error.value = '글을 불러오지 못했어요.'
  } finally {
    loading.value = false
  }
}

// 작성 중 이탈하면 확인
const isDirty = computed(() =>
  !saved.value && (title.value.trim() || content.value.trim() || selectedProducts.value.length),
)
onBeforeRouteLeave(async () => {
  if (!isDirty.value) return true
  return await confirm.ask({
    title: '작성을 그만둘까요?',
    message: '저장하지 않은 내용은 사라져요.',
    confirmText: '나가기', danger: true,
  })
})

onMounted(() => {
  if (isEdit.value) loadForEdit()
})
</script>

<template>
  <div class="screen">
    <div class="main">
      <header class="topbar">
        <button class="cancel" @click="cancel">취소</button>
        <span class="topbar-title">{{ isEdit ? '글 수정' : '새 글' }}</span>
        <button class="submit" :disabled="!canSubmit" @click="submit">{{ saving ? '저장 중…' : '완료' }}</button>
      </header>

      <div class="body">
        <p v-if="loading" class="msg">불러오는 중...</p>

        <template v-else>
          <!-- 카테고리 -->
          <div class="field">
            <span class="label">카테고리</span>
            <div class="cats">
              <button
                v-for="c in CATEGORIES" :key="c.key"
                class="cat-btn" :class="{ on: category === c.key }"
                @click="category = c.key"
              >{{ c.label }}</button>
            </div>
          </div>

          <!-- 제목 -->
          <div class="field">
            <span class="label">제목</span>
            <input v-model="title" class="title-input" placeholder="제목을 입력하세요" maxlength="200" />
          </div>

          <!-- 내용 -->
          <div class="field">
            <span class="label">내용</span>
            <textarea v-model="content" class="content-input" placeholder="내용을 입력하세요" rows="9" />
          </div>

          <!-- 제품 태그(선택, 여러 개 가능) -->
          <div class="field">
            <span class="label">제품 태그 <span class="optional">선택 · 여러 개 가능</span></span>

            <div v-if="selectedProducts.length" class="picked-list">
              <div v-for="sp in selectedProducts" :key="sp.id" class="picked">
                <div class="picked-img">
                  <img v-if="sp.image" :src="sp.image" :alt="sp.name" />
                  <span v-else class="picked-ph"><Icon name="leaf" :size="22" /></span>
                </div>
                <div class="picked-meta">
                  <p class="picked-brand">{{ sp.brand }}</p>
                  <p class="picked-name">{{ sp.name }}</p>
                </div>
                <button class="picked-clear" @click="removeProduct(sp.id)" aria-label="태그 제거"><Icon name="x" :size="14" /></button>
              </div>
            </div>

            <div class="picker">
              <Icon name="search" :size="16" class="picker-ic" />
              <input
                v-model="productQuery"
                class="picker-input"
                placeholder="제품·브랜드 검색해 태그 추가"
                @focus="focusPicker"
              />
              <ul v-if="pickerOpen && productQuery.trim()" class="picker-results">
                <li v-if="!productsLoaded" class="picker-msg">검색 중…</li>
                <li v-else-if="!productResults.length" class="picker-msg">검색 결과가 없어요.</li>
                <li
                  v-for="p in productResults" :key="p.id"
                  class="picker-item" @click="pickProduct(p)"
                >
                  <span class="pi-brand">{{ p.brand }}</span>
                  <span class="pi-name">{{ p.name }}</span>
                </li>
              </ul>
            </div>
          </div>

          <p v-if="error" class="err">{{ error }}</p>
        </template>
      </div>
    </div>

    <GlobalSidebar />
  </div>
</template>

<style scoped>
.screen { height: 100%; display: flex; flex-direction: column; overflow: hidden; }
.main { flex: 1; min-height: 0; display: flex; flex-direction: column; overflow: hidden; }

.topbar {
  flex-shrink: 0; display: flex; align-items: center; justify-content: space-between;
  padding: calc(10px + env(safe-area-inset-top)) 16px 10px; border-bottom: 1px solid var(--line-soft);
}
.cancel { font-size: 14px; color: var(--ink-soft); padding: 6px 4px; }
.topbar-title { font-size: 15px; font-weight: 600; color: var(--ink); }
.submit { font-size: 14px; font-weight: 700; color: var(--sage-ink); padding: 6px 4px; }
.submit:disabled { color: var(--ink-faint); }

.body { flex: 1; min-height: 0; overflow-y: auto; padding: 18px 20px 40px; display: flex; flex-direction: column; gap: 22px; }
.msg { font-size: 13px; color: var(--ink-soft); padding: 30px 2px; text-align: center; }

.field { display: flex; flex-direction: column; gap: 9px; }
.label { font-size: 11px; letter-spacing: 2px; text-transform: uppercase; color: var(--ink-faint); font-weight: 600; }
.optional { letter-spacing: 0; text-transform: none; color: var(--sage); font-weight: 600; margin-left: 4px; }

.cats { display: flex; gap: 8px; }
.cat-btn {
  padding: 9px 18px; border-radius: 99px; font-size: 13.5px; font-weight: 600;
  color: var(--ink-soft); background: var(--sheet); border: 1px solid var(--line); transition: all var(--t-fast);
}
.cat-btn.on { background: var(--ink); color: var(--canvas); border-color: var(--ink); box-shadow: var(--sh-sm); }

.title-input, .content-input, .picker-input {
  width: 100%; padding: 13px 15px; border: 1px solid var(--line); border-radius: 14px;
  font-size: 14.5px; background: var(--card); color: var(--ink); outline: none; font-family: inherit;
  transition: border-color var(--t-fast), box-shadow var(--t-fast);
}
.content-input { line-height: 1.7; resize: vertical; min-height: 180px; }
.title-input:focus, .content-input:focus, .picker-input:focus {
  border-color: var(--sage); box-shadow: 0 0 0 3px rgba(126,139,109,.15);
}
.title-input::placeholder, .content-input::placeholder, .picker-input::placeholder { color: var(--ink-faint); }

.picker { position: relative; }
.picker-ic { position: absolute; top: 50%; left: 14px; transform: translateY(-50%); color: var(--ink-faint); pointer-events: none; z-index: 1; }
.picker .picker-input { padding-left: 40px; }
.picker-results {
  position: absolute; top: calc(100% + 6px); left: 0; right: 0; z-index: 6;
  background: var(--card); border: 1px solid var(--line); border-radius: 14px; box-shadow: var(--sh-lg);
  overflow: hidden; max-height: 280px; overflow-y: auto;
}
.picker-msg { padding: 14px 16px; font-size: 13px; color: var(--ink-faint); }
.picker-item {
  display: flex; flex-direction: column; gap: 2px; padding: 11px 16px; cursor: pointer;
  border-bottom: 1px solid var(--line-soft); transition: background var(--t-fast);
}
.picker-item:last-child { border-bottom: none; }
.picker-item:hover { background: var(--sheet); }
.pi-brand { font-size: 10.5px; letter-spacing: 1px; text-transform: uppercase; color: var(--ink-faint); }
.pi-name { font-size: 13.5px; font-weight: 600; color: var(--ink); }

.picked-list { display: flex; flex-direction: column; gap: 8px; margin-bottom: 10px; }
.picked {
  display: flex; align-items: center; gap: 12px; padding: 11px 12px;
  border-radius: 14px; background: var(--sage-soft); border: 1px solid transparent;
}
.picked-img {
  width: 48px; height: 48px; flex-shrink: 0; border-radius: 10px; overflow: hidden;
  background: var(--card); display: flex; align-items: center; justify-content: center;
}
.picked-img img { width: 100%; height: 100%; object-fit: cover; }
.picked-ph { display: flex; color: var(--sage); opacity: .55; }
.picked-meta { flex: 1; min-width: 0; }
.picked-brand { font-size: 10.5px; letter-spacing: 1px; text-transform: uppercase; color: var(--ink-faint); }
.picked-name { font-size: 13.5px; font-weight: 600; color: var(--ink); white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
.picked-clear { width: 26px; height: 26px; border-radius: 50%; background: rgba(0,0,0,.06); color: var(--ink-soft); display: flex; align-items: center; justify-content: center; flex-shrink: 0; }

.err { font-size: 13px; color: var(--danger); }

/* ── 데스크탑(≥900px) ── */
@media (min-width: 900px) {
  .screen { flex-direction: row; }
  .topbar, .body { max-width: 720px; width: 100%; margin-left: auto; margin-right: auto; }
  .topbar { padding: 24px 40px 14px; }
  .body { padding: 28px 40px 40px; }
}
</style>
