<script setup>
import { ref, onMounted } from 'vue'
import { useProfileStore } from '@/stores/profile'

const profile = useProfileStore()

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
  try {
    await profile.patchProfile({
      skinType: editSkinType.value,
      concerns: editConcerns.value,
      avoidIngredients: editAvoidList.value,
    })
    editing.value = false
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
    <div class="page-header">
      <div>
        <h2 class="page-title">피부 프로필</h2>
        <p class="page-desc">챗봇이 추천할 때 자동으로 참조하는 정보입니다.</p>
      </div>
      <button v-if="!editing" class="edit-btn" @click="startEdit">✏️ 수정</button>
      <div v-else class="edit-actions">
        <button class="cancel-btn" :disabled="saving" @click="cancelEdit">취소</button>
        <button class="save-btn" :disabled="saving" @click="saveEdit">{{ saving ? '저장 중...' : '저장' }}</button>
      </div>
    </div>

    <p v-if="errorMsg" class="error-msg">{{ errorMsg }}</p>
    <p v-if="loading" class="loading-msg">프로필을 불러오는 중...</p>

    <!-- 보기 모드 -->
    <div v-if="!editing" class="cards">
      <div class="profile-card">
        <p class="card-label">피부 타입</p>
        <p class="card-value">{{ profile.skinType }}</p>
      </div>
      <div class="profile-card">
        <p class="card-label">피부 고민</p>
        <div class="tags">
          <span v-for="c in profile.concerns" :key="c" class="tag">{{ c }}</span>
        </div>
      </div>
      <div class="profile-card">
        <p class="card-label">기피 성분</p>
        <div class="tags">
          <span v-for="i in profile.avoidIngredients" :key="i" class="tag">{{ i }}</span>
          <span v-if="!profile.avoidIngredients.length" class="no-data">없음</span>
        </div>
      </div>
    </div>

    <!-- 편집 모드 -->
    <div v-else class="edit-form">
      <div class="edit-section">
        <p class="edit-label">피부 타입</p>
        <div class="type-btns">
          <button
            v-for="t in SKIN_TYPES" :key="t"
            class="type-btn"
            :class="{ selected: editSkinType === t }"
            @click="editSkinType = t"
          >{{ t }}</button>
        </div>
      </div>

      <div class="edit-section">
        <p class="edit-label">피부 고민</p>
        <div class="tags-row">
          <button
            v-for="c in CONCERNS" :key="c"
            class="tag-btn"
            :class="{ selected: editConcerns.includes(c) }"
            @click="toggleConcern(c)"
          >{{ c }}</button>
        </div>
      </div>

      <div class="edit-section">
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
      </div>
    </div>
  </div>
</template>

<style scoped>
.view { max-width: 600px; width: 100%; margin: 0 auto; }

.page-header {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  margin-bottom: 24px;
}
.page-title { font-size: 20px; font-weight: 700; margin-bottom: 4px; }
.page-desc { font-size: 13px; color: var(--text-secondary); }

.error-msg { font-size: 13px; color: var(--danger); margin-bottom: 12px; }
.loading-msg { font-size: 13px; color: var(--text-muted); margin-bottom: 12px; }

.save-btn:disabled, .cancel-btn:disabled { opacity: 0.5; cursor: default; }

.edit-btn {
  padding: 8px 16px;
  border: 1px solid var(--border);
  border-radius: 8px;
  background: var(--surface);
  font-size: 13px;
  cursor: pointer;
  transition: background 0.15s;
}
.edit-btn:hover { background: var(--bg); }

.edit-actions { display: flex; gap: 8px; }
.cancel-btn {
  padding: 8px 16px;
  border: 1px solid var(--border);
  border-radius: 8px;
  background: var(--surface);
  font-size: 13px;
  cursor: pointer;
}
.save-btn {
  padding: 8px 16px;
  border: none;
  border-radius: 8px;
  background: var(--text-primary);
  color: #fff;
  font-size: 13px;
  cursor: pointer;
}

.cards { display: flex; flex-direction: column; gap: 12px; }

.profile-card {
  background: var(--bg);
  border-radius: 12px;
  padding: 16px 20px;
  display: flex;
  flex-direction: column;
  gap: 8px;
}
.card-label { font-size: 12px; color: var(--text-muted); }
.card-value { font-size: 16px; font-weight: 600; }

.tags { display: flex; flex-wrap: wrap; gap: 8px; }
.tag {
  padding: 5px 12px;
  background: var(--surface);
  border: 1px solid var(--border);
  border-radius: 20px;
  font-size: 13px;
}
.no-data { font-size: 13px; color: var(--text-muted); }

/* Edit form */
.edit-form { display: flex; flex-direction: column; gap: 24px; }
.edit-section { display: flex; flex-direction: column; gap: 10px; }
.edit-label { font-size: 13px; font-weight: 500; color: var(--text-secondary); }

.type-btns { display: flex; gap: 8px; }
.type-btn {
  padding: 8px 16px;
  border-radius: 20px;
  border: 1px solid var(--border);
  background: var(--surface);
  font-size: 14px;
  cursor: pointer;
  transition: all 0.15s;
}
.type-btn:hover, .type-btn.selected { background: var(--text-primary); color: #fff; border-color: var(--text-primary); }

.tags-row { display: flex; flex-wrap: wrap; gap: 8px; }
.tag-btn {
  padding: 6px 14px;
  border-radius: 20px;
  border: 1px solid var(--border);
  background: var(--surface);
  font-size: 13px;
  cursor: pointer;
  transition: all 0.15s;
}
.tag-btn:hover, .tag-btn.selected { background: var(--text-primary); color: #fff; border-color: var(--text-primary); }

.avoid-tags { display: flex; flex-wrap: wrap; gap: 6px; min-height: 28px; }
.avoid-tag {
  display: flex;
  align-items: center;
  gap: 4px;
  padding: 4px 10px;
  background: var(--tag-bg);
  border-radius: 20px;
  font-size: 13px;
}
.remove-tag { border: none; background: none; color: var(--text-muted); font-size: 14px; cursor: pointer; }

.avoid-input-row { display: flex; gap: 8px; }
.avoid-input-row input {
  flex: 1;
  padding: 8px 12px;
  border: 1px solid var(--border);
  border-radius: 8px;
  font-size: 14px;
  outline: none;
}
.avoid-input-row input:focus { border-color: var(--text-primary); }
.add-btn {
  padding: 8px 16px;
  background: var(--text-primary);
  color: #fff;
  border: none;
  border-radius: 8px;
  font-size: 13px;
  cursor: pointer;
}
</style>
