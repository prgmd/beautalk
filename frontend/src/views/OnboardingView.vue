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

async function finishOnboarding() {
  profile.update({
    skinType: selectedSkinType.value,
    concerns: selectedConcerns.value,
    avoidIngredients: avoidList.value,
  })
  auth.setProfileComplete()

  messages.value.push({ id: Date.now(), role: 'user', type: 'text', text: avoidList.value.length ? avoidList.value.join(', ') : '없어요' })
  await nextTick()

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
              <button class="confirm-btn" @click="finishOnboarding">완료</button>
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
}

.header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 16px 24px;
  border-bottom: 1px solid var(--border);
  background: var(--surface);
}

.header-title { font-size: 15px; font-weight: 600; }

.progress-wrap { display: flex; align-items: center; gap: 12px; }
.progress-label { font-size: 13px; color: var(--text-secondary); }
.progress-bar { width: 120px; height: 4px; background: var(--border); border-radius: 2px; }
.progress-fill { height: 100%; background: var(--text-primary); border-radius: 2px; transition: width 0.4s; }

.chat-body {
  flex: 1;
  overflow-y: auto;
  padding: 24px;
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.msg-row {
  display: flex;
  gap: 10px;
  align-items: flex-start;
}
.msg-row.user { flex-direction: row-reverse; }

.ai-avatar {
  width: 32px;
  height: 32px;
  border-radius: 50%;
  background: var(--ai-avatar);
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 12px;
  font-weight: 700;
  flex-shrink: 0;
}

.bubble-wrap { display: flex; flex-direction: column; gap: 10px; max-width: 480px; }

.bubble {
  padding: 12px 16px;
  border-radius: 16px;
  font-size: 14px;
  line-height: 1.6;
  white-space: pre-line;
}
.bubble.ai { background: var(--ai-bubble); color: var(--ai-bubble-fg); border-top-left-radius: 4px; }
.bubble.user { background: var(--user-bubble); color: var(--user-bubble-fg); border-top-right-radius: 4px; }
.bubble.complete { background: var(--success-bg); color: var(--success-fg); }

.skin-type-btns { display: flex; flex-wrap: wrap; gap: 8px; }
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

.concerns-wrap, .avoid-wrap { display: flex; flex-direction: column; gap: 10px; }

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

.confirm-btn {
  align-self: flex-start;
  padding: 8px 20px;
  background: var(--text-primary);
  color: #fff;
  border: none;
  border-radius: 8px;
  font-size: 14px;
  transition: opacity 0.15s;
}
.confirm-btn:disabled { opacity: 0.4; cursor: default; }

.avoid-tags { display: flex; flex-wrap: wrap; gap: 6px; }
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
  font-size: 14px;
}

.input-bar {
  padding: 16px 24px;
  border-top: 1px solid var(--border);
  background: var(--surface);
}

.input-placeholder input {
  width: 100%;
  padding: 12px 16px;
  border: 1px solid var(--border);
  border-radius: 10px;
  font-size: 14px;
  background: var(--bg);
  color: var(--text-muted);
  outline: none;
}

.go-chat-btn {
  width: 100%;
  padding: 14px;
  background: var(--text-primary);
  color: #fff;
  border: none;
  border-radius: 10px;
  font-size: 15px;
  font-weight: 600;
}
</style>
