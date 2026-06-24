<script setup>
import { ref, onMounted } from 'vue'
import { useProfileStore } from '@/stores/profile'
import { useToastStore } from '@/stores/toast'

const profile = useProfileStore()
const toast = useToastStore()

const editing = ref(false)
const loading = ref(false)
const saving = ref(false)
const errorMsg = ref('')

const SKIN_TYPES = ['건성', '지성', '복합성', '민감성']
const CONCERNS = ['여드름', '주름', '색소침착', '모공', '트러블', '건조함', '민감성', '탄력']

const editSkinType = ref('')
const editConcerns = ref([])
const editAvoidInput = ref('')
const editAvoidList = ref([])

// 진입 시 백엔드에서 최신 프로필 로드 (이미 로드됐으면 생략)
onMounted(async () => {
  if (profile.loaded) return
  loading.value = true
  try {
    await profile.fetchProfile()
  } catch {
    errorMsg.value = '프로필을 불러오지 못했어요.'
  }
  loading.value = false
})

function startEdit() {
  editSkinType.value = profile.skinType
  editConcerns.value = [...profile.concerns]
  editAvoidList.value = [...profile.avoidIngredients]
  errorMsg.value = ''
  editing.value = true
}

function cancelEdit() { editing.value = false }

async function saveEdit() {
  if (saving.value) return
  saving.value = true
  errorMsg.value = ''
  // 입력칸에 남아있는(추가 안 누른) 기피 성분도 반영
  const pending = editAvoidInput.value.trim()
  if (pending && !editAvoidList.value.includes(pending)) editAvoidList.value.push(pending)
  editAvoidInput.value = ''
  try {
    await profile.patchProfile({
      skinType: editSkinType.value,
      concerns: editConcerns.value,
      avoidIngredients: editAvoidList.value,
    })
    editing.value = false
    toast.success('피부 프로필을 저장했어요')
  } catch {
    errorMsg.value = '저장에 실패했어요. 잠시 후 다시 시도해 주세요.'
  }
  saving.value = false
}

function toggleConcern(c) {
  const idx = editConcerns.value.indexOf(c)
  if (idx === -1) editConcerns.value.push(c)
  else editConcerns.value.splice(idx, 1)
}

function addAvoid() {
  const val = editAvoidInput.value.trim()
  if (val && !editAvoidList.value.includes(val)) editAvoidList.value.push(val)
  editAvoidInput.value = ''
}

function removeAvoid(item) {
  editAvoidList.value = editAvoidList.value.filter(i => i !== item)
}
</script>

<template>
  <div class="view">
    <header class="page-header">
      <div class="header-text">
        <p class="eyebrow">My Skin · 피부 카르테</p>
        <h2 class="page-title serif">피부 프로필</h2>
        <p class="page-desc">챗봇이 추천할 때 <em>자동으로</em> 참조하는 정보입니다.</p>
      </div>
      <button v-if="!editing" class="edit-btn" @click="startEdit">수정</button>
      <div v-else class="edit-actions">
        <button class="cancel-btn" :disabled="saving" @click="cancelEdit">취소</button>
        <button class="save-btn" :disabled="saving" @click="saveEdit">{{ saving ? '저장 중...' : '저장' }}</button>
      </div>
    </header>

    <p v-if="errorMsg" class="error-msg">{{ errorMsg }}</p>
    <p v-if="loading" class="loading-msg">프로필을 불러오는 중...</p>

    <!-- 보기 모드 -->
    <div v-if="!editing" class="cards">
      <article class="profile-card">
        <span class="leaf" aria-hidden="true">❋</span>
        <p class="card-label">Skin Type</p>
        <p class="card-sub">피부 타입</p>
        <p class="card-value serif">{{ profile.skinType }}</p>
      </article>

      <article class="profile-card">
        <span class="leaf" aria-hidden="true">❋</span>
        <p class="card-label">Concerns</p>
        <p class="card-sub">피부 고민</p>
        <div class="tags">
          <span v-for="c in profile.concerns" :key="c" class="tag">{{ c }}</span>
          <span v-if="!profile.concerns.length" class="no-data">없음</span>
        </div>
      </article>

      <article class="profile-card">
        <span class="leaf" aria-hidden="true">❋</span>
        <p class="card-label">Avoid</p>
        <p class="card-sub">기피 성분</p>
        <div class="tags">
          <span v-for="i in profile.avoidIngredients" :key="i" class="tag">{{ i }}</span>
          <span v-if="!profile.avoidIngredients.length" class="no-data">없음</span>
        </div>
      </article>
    </div>

    <!-- 편집 모드 -->
    <div v-else class="edit-form">
      <section class="edit-section">
        <p class="edit-eyebrow">Skin Type</p>
        <p class="edit-label">피부 타입</p>
        <div class="type-btns">
          <button
            v-for="t in SKIN_TYPES" :key="t"
            class="type-btn"
            :class="{ selected: editSkinType === t }"
            @click="editSkinType = t"
          >{{ t }}</button>
        </div>
      </section>

      <section class="edit-section">
        <p class="edit-eyebrow">Concerns</p>
        <p class="edit-label">피부 고민</p>
        <div class="tags-row">
          <button
            v-for="c in CONCERNS" :key="c"
            class="tag-btn"
            :class="{ selected: editConcerns.includes(c) }"
            @click="toggleConcern(c)"
          >{{ c }}</button>
        </div>
      </section>

      <section class="edit-section">
        <p class="edit-eyebrow">Avoid</p>
        <p class="edit-label">기피 성분</p>
        <div class="avoid-tags">
          <span v-for="item in editAvoidList" :key="item" class="avoid-tag">
            {{ item }}
            <button class="remove-tag" @click="removeAvoid(item)">×</button>
          </span>
        </div>
        <div class="avoid-input-row">
          <input v-model="editAvoidInput" placeholder="성분 입력 후 엔터" @keyup.enter="addAvoid" />
          <button class="add-btn" @click="addAvoid">추가</button>
        </div>
      </section>
    </div>
  </div>
</template>

<style scoped>
.view { display: flex; flex-direction: column; }

/* Header */
.page-header {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 12px;
  margin-bottom: 20px;
  animation: bt-rise 0.4s var(--ease) both;
}
.header-text { min-width: 0; }
.eyebrow {
  font-size: 11px; font-weight: 700; letter-spacing: 1.4px; text-transform: uppercase;
  color: var(--sage-ink); margin-bottom: 6px;
}
.page-title { font-size: 26px; font-weight: 500; letter-spacing: -0.4px; line-height: 1.15; }
.page-desc { font-size: 13px; color: var(--ink-soft); margin-top: 6px; }
.page-desc em { font-style: italic; color: var(--sage-ink); }

.error-msg { font-size: 13px; color: var(--danger); margin-bottom: 12px; }
.loading-msg { font-size: 13px; color: var(--ink-faint); margin-bottom: 12px; }

/* Header buttons */
.edit-btn {
  flex-shrink: 0;
  padding: 8px 18px;
  border: 1px solid var(--line);
  border-radius: 99px;
  background: var(--sheet);
  font-size: 13px;
  font-weight: 600;
  color: var(--ink);
  cursor: pointer;
  box-shadow: var(--sh-sm);
  transition: transform var(--t-fast) var(--ease), box-shadow var(--t-fast) var(--ease);
}
.edit-btn:active { transform: scale(.98); }

.edit-actions { display: flex; gap: 8px; flex-shrink: 0; }
.cancel-btn {
  padding: 8px 16px;
  border: 1px solid var(--line);
  border-radius: 99px;
  background: var(--sheet);
  font-size: 13px;
  font-weight: 600;
  color: var(--ink);
  cursor: pointer;
  box-shadow: var(--sh-sm);
  transition: transform var(--t-fast) var(--ease);
}
.cancel-btn:active:not(:disabled) { transform: scale(.98); }
.save-btn {
  padding: 8px 20px;
  border: none;
  border-radius: 99px;
  background: var(--ink);
  color: var(--canvas);
  font-size: 13px;
  font-weight: 600;
  cursor: pointer;
  box-shadow: var(--sh-ink);
  transition: transform var(--t-fast) var(--ease);
}
.save-btn:active:not(:disabled) { transform: scale(.98); }
.save-btn:disabled, .cancel-btn:disabled { opacity: 0.5; cursor: default; box-shadow: none; transform: none; }

/* View-mode cards */
.cards { display: flex; flex-direction: column; gap: 14px; }

.profile-card {
  position: relative;
  overflow: hidden;
  background: var(--card);
  border: 1px solid var(--line-soft);
  border-radius: var(--radius-lg);
  padding: 20px 22px;
  display: flex;
  flex-direction: column;
  gap: 4px;
  box-shadow: var(--sh-sm);
  animation: bt-rise 0.45s var(--ease) both;
}
.profile-card:nth-child(1) { animation-delay: 0.04s; }
.profile-card:nth-child(2) { animation-delay: 0.1s; }
.profile-card:nth-child(3) { animation-delay: 0.16s; }
.leaf {
  position: absolute;
  top: -10px; right: -6px;
  font-size: 56px;
  line-height: 1;
  color: var(--sage-soft);
  pointer-events: none;
  user-select: none;
}
.card-label {
  font-size: 10px; font-weight: 700; letter-spacing: 1.4px; text-transform: uppercase;
  color: var(--sage-ink);
}
.card-sub { font-size: 11px; color: var(--ink-faint); margin-bottom: 8px; }
.card-value { font-size: 22px; font-weight: 500; color: var(--ink); }

.tags { display: flex; flex-wrap: wrap; gap: 8px; }
.tag {
  padding: 6px 14px;
  background: var(--sage-soft);
  border: 1px solid transparent;
  border-radius: 99px;
  font-size: 13px;
  font-weight: 600;
  color: var(--sage-ink);
}
.no-data { font-size: 13px; color: var(--ink-faint); font-style: italic; }

/* Edit form */
.edit-form { display: flex; flex-direction: column; gap: 26px; }
.edit-section {
  display: flex; flex-direction: column; gap: 12px;
  animation: bt-rise 0.45s var(--ease) both;
}
.edit-section:nth-child(1) { animation-delay: 0.04s; }
.edit-section:nth-child(2) { animation-delay: 0.1s; }
.edit-section:nth-child(3) { animation-delay: 0.16s; }
.edit-eyebrow {
  font-size: 10px; font-weight: 700; letter-spacing: 1.4px; text-transform: uppercase;
  color: var(--sage-ink); margin-bottom: -8px;
}
.edit-label { font-size: 15px; font-weight: 500; color: var(--ink); }

.type-btns, .tags-row { display: flex; flex-wrap: wrap; gap: 8px; }
.type-btn, .tag-btn {
  padding: 9px 18px;
  border-radius: 99px;
  border: 1px solid var(--line);
  background: var(--card);
  font-size: 14px;
  font-weight: 600;
  color: var(--ink);
  cursor: pointer;
  box-shadow: var(--sh-sm);
  transition: transform var(--t-fast) var(--ease), box-shadow var(--t-fast) var(--ease), background var(--t-fast) var(--ease), border-color var(--t-fast) var(--ease), color var(--t-fast) var(--ease);
}
.tag-btn { padding: 8px 16px; font-size: 13px; }
.type-btn:active, .tag-btn:active { transform: scale(.97); }
.type-btn.selected, .tag-btn.selected {
  background: var(--ink);
  color: var(--canvas);
  border-color: transparent;
  box-shadow: var(--sh-ink);
}

.avoid-tags { display: flex; flex-wrap: wrap; gap: 8px; min-height: 28px; }
.avoid-tag {
  display: flex;
  align-items: center;
  gap: 4px;
  padding: 6px 8px 6px 14px;
  background: var(--sage-soft);
  border-radius: 99px;
  font-size: 13px;
  font-weight: 600;
  color: var(--sage-ink);
  animation: bt-pop 0.25s var(--ease-back) both;
}
.remove-tag {
  border: none;
  background: none;
  color: var(--sage-ink);
  opacity: 0.6;
  font-size: 16px;
  line-height: 1;
  cursor: pointer;
  transition: opacity var(--t-fast) var(--ease);
}
.remove-tag:hover { opacity: 1; }

.avoid-input-row { display: flex; gap: 8px; }
.avoid-input-row input {
  flex: 1;
  min-width: 0;
  padding: 11px 16px;
  border: 1px solid var(--line);
  border-radius: var(--radius-sm);
  background: var(--card);
  font-size: 14px;
  color: var(--ink);
  outline: none;
  transition: border-color var(--t-fast) var(--ease), box-shadow var(--t-fast) var(--ease);
}
.avoid-input-row input::placeholder { color: var(--ink-faint); }
.avoid-input-row input:focus {
  border-color: var(--sage);
  box-shadow: 0 0 0 3px rgba(126,139,109,0.15);
}
.add-btn {
  flex-shrink: 0;
  padding: 10px 20px;
  background: var(--ink);
  color: var(--canvas);
  border: none;
  border-radius: 99px;
  font-size: 13px;
  font-weight: 600;
  cursor: pointer;
  box-shadow: var(--sh-ink);
  transition: transform var(--t-fast) var(--ease);
}
.add-btn:active { transform: scale(.98); }

/* ===== Desktop polish (≥900px) ===== */
@media (min-width: 900px) {
  .view { max-width: 860px; }

  .page-header { margin-bottom: 28px; }
  .page-title { font-size: 32px; }
  .page-desc { font-size: 14px; }

  /* View-mode cards: roomier 2-column grid, full-width concerns/avoid */
  .cards {
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 18px;
  }
  .profile-card { padding: 26px 28px; }
  .profile-card:nth-child(2),
  .profile-card:nth-child(3) { grid-column: 1 / -1; }
  .card-value { font-size: 26px; }

  /* Edit form: constrain reading width, roomier chip rows */
  .edit-form { max-width: 680px; gap: 30px; }
  .type-btns, .tags-row { gap: 10px; }
  .type-btn, .tag-btn { padding: 10px 20px; }
  .tag-btn { padding: 9px 18px; }
}
</style>
