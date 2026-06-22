<script setup>
import { ref, computed, nextTick } from 'vue'
import { useRouter } from 'vue-router'
import { useProfileStore } from '@/stores/profile'
import { useAuthStore } from '@/stores/auth'
import GlobalSidebar from '@/components/GlobalSidebar.vue'

const router = useRouter()
const profile = useProfileStore()
const auth = useAuthStore()

const SKIN_TYPES = ['건성', '지성', '복합성', '민감성']
const CONCERNS = ['여드름', '주름', '색소침착', '모공', '트러블', '건조함', '민감성', '탄력']

const step = ref(1)
const selectedSkinType = ref('')
const selectedConcerns = ref([])
const avoidInput = ref('')
const avoidList = ref([])

const messages = ref([
  { id: 1, role: 'ai', type: 'text', text: '안녕하세요! 맞춤 추천을 위해 몇 가지만 여쭤볼게요. 피부 타입이 어떻게 되세요?' }
])

const progress = computed(() => (step.value / 3) * 100)

async function selectSkinType(type) {
  selectedSkinType.value = type
  messages.value.push({ id: Date.now(), role: 'user', type: 'text', text: `${type}이에요` })
  await nextTick()
  scrollToBottom()

  setTimeout(async () => {
    step.value = 2
    messages.value.push({
      id: Date.now(),
      role: 'ai',
      type: 'concerns',
      text: '고민되는 부분이 있나요? 여러 개 선택해도 좋아요.',
    })
    await nextTick()
    scrollToBottom()
  }, 400)
}

function toggleConcern(c) {
  const idx = selectedConcerns.value.indexOf(c)
  if (idx === -1) selectedConcerns.value.push(c)
  else selectedConcerns.value.splice(idx, 1)
}

async function confirmConcerns() {
  if (!selectedConcerns.value.length) return
  messages.value.push({ id: Date.now(), role: 'user', type: 'text', text: selectedConcerns.value.join(', ') })
  await nextTick()
  scrollToBottom()

  setTimeout(async () => {
    step.value = 3
    messages.value.push({
      id: Date.now(),
      role: 'ai',
      type: 'avoid',
      text: '피해야 할 성분이 있나요? 없으면 건너뛰어도 괜찮아요.',
    })
    await nextTick()
    scrollToBottom()
  }, 400)
}

function addAvoid() {
  const val = avoidInput.value.trim()
  if (val && !avoidList.value.includes(val)) avoidList.value.push(val)
  avoidInput.value = ''
}

function removeAvoid(item) {
  avoidList.value = avoidList.value.filter(i => i !== item)
}

const saving = ref(false)
const saveError = ref('')

async function finishOnboarding() {
  if (saving.value) return
  profile.update({
    skinType: selectedSkinType.value,
    concerns: selectedConcerns.value,
    avoidIngredients: avoidList.value,
  })

  messages.value.push({ id: Date.now(), role: 'user', type: 'text', text: avoidList.value.length ? avoidList.value.join(', ') : '없어요' })
  await nextTick()
  scrollToBottom()

  // 백엔드에 프로필 저장
  saving.value = true
  saveError.value = ''
  try {
    await profile.saveProfile()
    auth.setProfileComplete()
  } catch {
    saveError.value = '프로필 저장에 실패했어요. 잠시 후 다시 시도해 주세요.'
    saving.value = false
    return
  }
  saving.value = false

  setTimeout(async () => {
    messages.value.push({
      id: Date.now(),
      role: 'ai',
      type: 'complete',
      text: '프로필 작성 완료! 이제 어떤 제품이 필요한지 말씀해 주세요.\n예: "여드름에 좋은 토너 추천해줘"',
    })
    step.value = 4
    await nextTick()
    scrollToBottom()
  }, 400)
}

function scrollToBottom() {
  const el = document.querySelector('.chat-body')
  if (el) el.scrollTop = el.scrollHeight
}

function goChat() {
  router.push('/chat')
}
</script>

<template>
  <div class="layout">
    <GlobalSidebar />

    <div class="main">
      <div class="header">
        <span class="header-title">프로필 설정</span>
        <div class="progress-wrap">
          <span class="progress-label">{{ Math.min(step, 3) }}/3 완료</span>
          <div class="progress-bar">
            <div class="progress-fill" :style="{ width: Math.min(progress, 100) + '%' }" />
          </div>
        </div>
      </div>

      <div class="chat-body">
        <div v-for="msg in messages" :key="msg.id" class="msg-row" :class="msg.role">

          <div v-if="msg.role === 'ai'" class="ai-avatar">B</div>

          <div class="bubble-wrap">
            <div class="bubble" :class="[msg.role, msg.type === 'complete' ? 'complete' : '']">
              {{ msg.text }}
            </div>

            <!-- 피부 타입 선택 버튼 (step 1) -->
            <div v-if="msg.type === 'text' && msg.role === 'ai' && step === 1" class="skin-type-btns">
              <button
                v-for="t in SKIN_TYPES" :key="t"
                class="type-btn"
                :class="{ selected: selectedSkinType === t }"
                @click="selectSkinType(t)"
              >{{ t }}</button>
            </div>

            <!-- 피부 고민 다중 선택 (step 2) -->
            <div v-if="msg.type === 'concerns'" class="concerns-wrap">
              <div class="tags-row">
                <button
                  v-for="c in CONCERNS" :key="c"
                  class="tag-btn"
                  :class="{ selected: selectedConcerns.includes(c) }"
                  @click="toggleConcern(c)"
                >{{ c }}</button>
              </div>
              <button class="confirm-btn" :disabled="!selectedConcerns.length" @click="confirmConcerns">확인</button>
            </div>

            <!-- 기피 성분 입력 (step 3) -->
            <div v-if="msg.type === 'avoid'" class="avoid-wrap">
              <div class="avoid-tags">
                <span v-for="item in avoidList" :key="item" class="avoid-tag">
                  {{ item }}
                  <button class="remove-tag" @click="removeAvoid(item)">×</button>
                </span>
              </div>
              <div class="avoid-input-row">
                <input
                  v-model="avoidInput"
                  placeholder="성분 입력 (예: 알코올)"
                  @keyup.enter="addAvoid"
                />
                <button class="add-btn" @click="addAvoid">추가</button>
              </div>
              <button class="confirm-btn" :disabled="saving" @click="finishOnboarding">
                {{ saving ? '저장 중...' : '완료' }}
              </button>
              <p v-if="saveError" class="save-error">{{ saveError }}</p>
            </div>
          </div>
        </div>
      </div>

      <!-- 완료 후 채팅 이동 버튼 -->
      <div class="input-bar">
        <button v-if="step === 4" class="go-chat-btn" @click="goChat">
          추천 받으러 가기 →
        </button>
        <div v-else class="input-placeholder">
          <input type="text" placeholder="메시지를 입력하세요" disabled />
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.layout { display: flex; height: 100vh; background: var(--bg); }

.main {
  flex: 1;
  display: flex;
  flex-direction: column;
  overflow: hidden;
  position: relative;
}

/* subtle brand glow behind the conversation */
.main::before {
  content: "";
  position: absolute;
  top: -120px;
  right: -100px;
  width: 360px;
  height: 360px;
  background: var(--gradient-brand);
  opacity: 0.10;
  filter: blur(80px);
  border-radius: 50%;
  pointer-events: none;
  z-index: 0;
}

.header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 16px 24px;
  border-bottom: 1px solid var(--border);
  background: color-mix(in srgb, var(--surface) 80%, transparent);
  backdrop-filter: blur(8px);
  position: relative;
  z-index: 1;
}

.header-title {
  font-size: 15px;
  font-weight: 700;
  letter-spacing: -0.01em;
}

.progress-wrap { display: flex; align-items: center; gap: 12px; }
.progress-label {
  font-size: 13px;
  font-weight: 600;
  color: var(--text-secondary);
}
.progress-bar {
  width: 140px;
  height: 6px;
  background: var(--border);
  border-radius: 999px;
  overflow: hidden;
}
.progress-fill {
  height: 100%;
  background: var(--gradient-brand);
  border-radius: 999px;
  box-shadow: var(--shadow-glow);
  transition: width var(--t-slow) var(--ease);
}

.chat-body {
  flex: 1;
  overflow-y: auto;
  padding: 28px 24px;
  display: flex;
  flex-direction: column;
  gap: 18px;
  position: relative;
  z-index: 1;
}

.msg-row {
  display: flex;
  gap: 10px;
  align-items: flex-start;
  animation: bt-rise 0.4s var(--ease) both;
}
.msg-row.user { flex-direction: row-reverse; }

.ai-avatar {
  width: 34px;
  height: 34px;
  border-radius: 50%;
  background: var(--gradient-brand);
  color: #fff;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 13px;
  font-weight: 700;
  flex-shrink: 0;
  box-shadow: var(--shadow-sm);
}

.bubble-wrap { display: flex; flex-direction: column; gap: 12px; max-width: 480px; }

.bubble {
  padding: 13px 17px;
  border-radius: var(--radius-lg);
  font-size: 14px;
  line-height: 1.6;
  white-space: pre-line;
  box-shadow: var(--shadow-sm);
}
.bubble.ai {
  background: var(--ai-bubble);
  color: var(--ai-bubble-fg);
  border-top-left-radius: 6px;
}
.bubble.user {
  background: var(--gradient-ink);
  color: #fff;
  border-top-right-radius: 6px;
}
.bubble.complete {
  background: var(--gradient-brand);
  color: #fff;
  box-shadow: var(--shadow-glow);
}

.skin-type-btns { display: flex; flex-wrap: wrap; gap: 8px; }
.type-btn {
  padding: 9px 18px;
  border-radius: 999px;
  border: 1px solid var(--border);
  background: var(--surface);
  color: var(--text-primary);
  font-size: 14px;
  font-weight: 600;
  cursor: pointer;
  box-shadow: var(--shadow-sm);
  transition: transform var(--t-fast) var(--ease),
    box-shadow var(--t-fast) var(--ease),
    border-color var(--t-fast) var(--ease),
    background var(--t-fast) var(--ease);
}
.type-btn:hover {
  transform: translateY(-2px);
  box-shadow: var(--shadow-md);
  border-color: var(--brand-1);
}
.type-btn.selected {
  background: var(--gradient-brand);
  color: #fff;
  border-color: transparent;
  box-shadow: var(--shadow-glow);
}

.concerns-wrap, .avoid-wrap { display: flex; flex-direction: column; gap: 12px; }

.tags-row { display: flex; flex-wrap: wrap; gap: 8px; }
.tag-btn {
  padding: 7px 16px;
  border-radius: 999px;
  border: 1px solid var(--border);
  background: var(--surface);
  color: var(--text-primary);
  font-size: 13px;
  font-weight: 600;
  cursor: pointer;
  box-shadow: var(--shadow-sm);
  transition: transform var(--t-fast) var(--ease),
    box-shadow var(--t-fast) var(--ease),
    border-color var(--t-fast) var(--ease),
    background var(--t-fast) var(--ease);
}
.tag-btn:hover {
  transform: translateY(-2px);
  box-shadow: var(--shadow-md);
  border-color: var(--brand-1);
}
.tag-btn.selected {
  background: var(--gradient-brand);
  color: #fff;
  border-color: transparent;
  box-shadow: var(--shadow-glow);
}

.confirm-btn {
  align-self: flex-start;
  padding: 10px 24px;
  background: var(--gradient-brand);
  color: #fff;
  border: none;
  border-radius: var(--radius);
  font-size: 14px;
  font-weight: 600;
  cursor: pointer;
  box-shadow: var(--shadow-sm);
  transition: transform var(--t-fast) var(--ease),
    box-shadow var(--t-fast) var(--ease), opacity var(--t-fast) var(--ease);
}
.confirm-btn:hover:not(:disabled) {
  transform: translateY(-2px);
  box-shadow: var(--shadow-glow);
}
.confirm-btn:active:not(:disabled) { transform: scale(0.98); }
.confirm-btn:disabled {
  opacity: 0.4;
  cursor: default;
  box-shadow: none;
}

.save-error { font-size: 13px; color: var(--danger); }

.avoid-tags { display: flex; flex-wrap: wrap; gap: 6px; }
.avoid-tag {
  display: flex;
  align-items: center;
  gap: 4px;
  padding: 5px 12px;
  background: var(--brand-soft);
  color: var(--brand);
  border-radius: 999px;
  font-size: 13px;
  font-weight: 600;
  animation: bt-pop 0.3s var(--ease-back) both;
}
.remove-tag {
  border: none;
  background: none;
  color: var(--brand);
  font-size: 15px;
  line-height: 1;
  cursor: pointer;
  opacity: 0.7;
  transition: opacity var(--t-fast) var(--ease);
}
.remove-tag:hover { opacity: 1; }

.avoid-input-row { display: flex; gap: 8px; }
.avoid-input-row input {
  flex: 1;
  padding: 10px 14px;
  border: 1px solid var(--border);
  border-radius: var(--radius);
  font-size: 14px;
  background: var(--surface);
  outline: none;
  transition: border-color var(--t-fast) var(--ease),
    box-shadow var(--t-fast) var(--ease);
}
.avoid-input-row input:focus {
  border-color: var(--brand-1);
  box-shadow: 0 0 0 3px rgba(255, 143, 177, 0.15);
}
.add-btn {
  padding: 10px 18px;
  background: var(--surface);
  color: var(--brand);
  border: 1px solid var(--border);
  border-radius: var(--radius);
  font-size: 14px;
  font-weight: 600;
  cursor: pointer;
  transition: transform var(--t-fast) var(--ease),
    box-shadow var(--t-fast) var(--ease),
    border-color var(--t-fast) var(--ease);
}
.add-btn:hover {
  transform: translateY(-2px);
  box-shadow: var(--shadow-md);
  border-color: var(--brand-1);
}
.add-btn:active { transform: scale(0.98); }

.input-bar {
  padding: 16px 24px;
  border-top: 1px solid var(--border);
  background: var(--surface);
  position: relative;
  z-index: 1;
}

.input-placeholder input {
  width: 100%;
  padding: 13px 16px;
  border: 1px solid var(--border);
  border-radius: var(--radius);
  font-size: 14px;
  background: var(--bg);
  color: var(--text-muted);
  outline: none;
}

.go-chat-btn {
  width: 100%;
  padding: 15px;
  background: var(--gradient-brand);
  color: #fff;
  border: none;
  border-radius: var(--radius);
  font-size: 15px;
  font-weight: 700;
  cursor: pointer;
  box-shadow: var(--shadow-sm);
  animation: bt-pop 0.4s var(--ease-back) both;
  transition: transform var(--t-fast) var(--ease),
    box-shadow var(--t-fast) var(--ease);
}
.go-chat-btn:hover {
  transform: translateY(-2px);
  box-shadow: var(--shadow-glow);
}
.go-chat-btn:active { transform: scale(0.98); }
</style>
