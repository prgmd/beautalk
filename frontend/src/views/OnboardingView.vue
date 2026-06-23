<script setup>
import { ref, computed, nextTick } from 'vue'
import { useRouter } from 'vue-router'
import { useProfileStore } from '@/stores/profile'
import { useAuthStore } from '@/stores/auth'

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
  <div class="screen">
    <!-- 앱바 + 진행 -->
    <header class="appbar">
      <div class="ab-top">
        <span class="eyebrow">your profile</span>
        <span class="ab-step">{{ Math.min(step, 3) }} <span class="ab-of">/ 3</span></span>
      </div>
      <h1 class="ab-title serif">맞춤 추천을 위한<br><em>몇 가지 질문</em></h1>
      <div class="progress-bar">
        <div class="progress-fill" :style="{ width: Math.min(progress, 100) + '%' }" />
      </div>
    </header>

    <div class="chat-body">
      <!-- 장식 새싹 -->
      <svg class="sprig" viewBox="0 0 60 120" fill="none" aria-hidden="true">
        <path d="M30 118 C30 80 30 50 30 14" stroke="currentColor" stroke-width="1.2" stroke-linecap="round"/>
        <path d="M30 70 C18 64 10 52 10 38 C24 42 30 56 30 70Z" fill="currentColor" opacity=".5"/>
        <path d="M30 52 C42 46 50 34 50 20 C36 24 30 38 30 52Z" fill="currentColor" opacity=".5"/>
        <path d="M30 32 C20 28 14 18 14 8 C26 11 30 22 30 32Z" fill="currentColor" opacity=".5"/>
      </svg>

      <div v-for="msg in messages" :key="msg.id" class="msg-row" :class="msg.role">

        <div v-if="msg.role === 'ai'" class="ai-avatar">🌿</div>

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
            <span class="field-label">고민 (복수 선택)</span>
            <div class="tags-row">
              <button
                v-for="c in CONCERNS" :key="c"
                class="tag-btn"
                :class="{ selected: selectedConcerns.includes(c) }"
                @click="toggleConcern(c)"
              >{{ c }}</button>
            </div>
            <button class="cta" :disabled="!selectedConcerns.length" @click="confirmConcerns">확인</button>
          </div>

          <!-- 기피 성분 입력 (step 3) -->
          <div v-if="msg.type === 'avoid'" class="avoid-wrap">
            <div v-if="avoidList.length" class="avoid-tags">
              <span v-for="item in avoidList" :key="item" class="avoid-tag">
                {{ item }}
                <button class="remove-tag" @click="removeAvoid(item)" aria-label="삭제">×</button>
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
            <button class="cta" :disabled="saving" @click="finishOnboarding">
              {{ saving ? '저장 중…' : '완료' }}
            </button>
            <p v-if="saveError" class="save-error">{{ saveError }}</p>
          </div>
        </div>
      </div>
    </div>

    <!-- 하단 바: 완료 후 채팅 이동 -->
    <div class="input-bar">
      <button v-if="step === 4" class="go-chat-btn" @click="goChat">
        추천 받으러 가기 →
      </button>
      <div v-else class="input-placeholder">
        <input type="text" placeholder="질문에 답하면 다음으로 넘어가요" disabled />
      </div>
    </div>
  </div>
</template>

<style scoped>
.screen {
  height: 100%;
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

/* ── 앱바 + 진행 ── */
.appbar {
  flex-shrink: 0;
  padding: calc(14px + env(safe-area-inset-top)) 20px 14px;
}
.ab-top {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 8px;
}
.eyebrow {
  font-size: 10px;
  letter-spacing: 4px;
  text-transform: uppercase;
  color: var(--sage);
}
.ab-step {
  font-family: 'Fraunces', 'Noto Serif KR', serif;
  font-size: 17px;
  color: var(--ink);
  letter-spacing: -.3px;
}
.ab-of { color: var(--ink-faint); font-size: 13px; }
.ab-title {
  font-size: 23px;
  font-weight: 400;
  line-height: 1.25;
  letter-spacing: -.3px;
  margin-bottom: 14px;
}
.ab-title em { font-style: italic; }

.progress-bar {
  height: 5px;
  background: var(--line-soft);
  border-radius: 999px;
  overflow: hidden;
}
.progress-fill {
  height: 100%;
  background: linear-gradient(90deg, var(--sage), var(--rose));
  border-radius: 999px;
  transition: width var(--t-slow) var(--ease);
}

/* ── 대화 본문 ── */
.chat-body {
  position: relative;
  flex: 1;
  min-height: 0;
  overflow-y: auto;
  padding: 22px 20px 8px;
  display: flex;
  flex-direction: column;
  gap: 18px;
}

/* 장식 새싹 */
.sprig {
  position: absolute;
  top: 8px;
  right: 14px;
  width: 38px;
  height: 76px;
  color: var(--sage);
  opacity: .22;
  pointer-events: none;
}

.msg-row {
  display: flex;
  gap: 9px;
  align-items: flex-start;
  animation: bt-rise .35s var(--ease) both;
}
.msg-row.user { flex-direction: row-reverse; }

.ai-avatar {
  width: 32px;
  height: 32px;
  border-radius: 50%;
  flex-shrink: 0;
  background: var(--sage-soft);
  border: 1px solid var(--line);
  box-shadow: var(--sh-sm);
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 15px;
}

.bubble-wrap {
  display: flex;
  flex-direction: column;
  gap: 12px;
  max-width: 82%;
}
.msg-row.user .bubble-wrap { align-items: flex-end; }

.bubble {
  padding: 12px 15px;
  border-radius: 17px;
  font-size: 14.5px;
  line-height: 1.6;
  white-space: pre-line;
}
.bubble.ai {
  background: var(--card);
  color: var(--ink);
  border: 1px solid var(--line-soft);
  border-bottom-left-radius: 5px;
  box-shadow: var(--sh-bub);
}
.bubble.user {
  background: var(--ink);
  color: var(--canvas);
  border-bottom-right-radius: 5px;
  box-shadow: var(--sh-ink);
}
.bubble.complete {
  background: var(--sage);
  color: var(--canvas);
  border: none;
  box-shadow: var(--sh-md);
}

/* ── 옵션 칩 공통 ── */
.field-label {
  font-size: 10px;
  letter-spacing: 2.5px;
  text-transform: uppercase;
  color: var(--ink-faint);
}

.skin-type-btns,
.tags-row { display: flex; flex-wrap: wrap; gap: 8px; }
.concerns-wrap,
.avoid-wrap { display: flex; flex-direction: column; gap: 12px; }

.type-btn,
.tag-btn {
  padding: 10px 18px;
  min-height: 40px;
  border-radius: 99px;
  border: 1px solid var(--line-soft);
  background: var(--card);
  color: var(--ink);
  font-size: 13.5px;
  font-weight: 500;
  box-shadow: var(--sh-sm);
  transition: transform var(--t-fast) var(--ease),
    background var(--t-fast) var(--ease),
    color var(--t-fast) var(--ease),
    box-shadow var(--t-fast) var(--ease);
}
.type-btn:active,
.tag-btn:active { transform: scale(.98); }
.type-btn.selected,
.tag-btn.selected {
  background: var(--ink);
  color: var(--canvas);
  border-color: transparent;
  box-shadow: var(--sh-ink);
}

/* ── 1차 CTA ── */
.cta {
  align-self: flex-start;
  padding: 12px 26px;
  min-height: 44px;
  background: var(--ink);
  color: var(--canvas);
  border-radius: 99px;
  font-size: 14px;
  font-weight: 600;
  box-shadow: var(--sh-ink);
  transition: transform var(--t-fast) var(--ease), opacity var(--t-fast) var(--ease);
}
.cta:not(:disabled):active { transform: scale(.98); }
.cta:disabled {
  opacity: .35;
  background: var(--ink-faint);
  box-shadow: none;
  cursor: default;
}

.save-error { font-size: 13px; color: var(--danger); }

/* ── 기피 성분 ── */
.avoid-tags { display: flex; flex-wrap: wrap; gap: 6px; }
.avoid-tag {
  display: inline-flex;
  align-items: center;
  gap: 5px;
  padding: 6px 8px 6px 13px;
  background: var(--rose-soft);
  color: var(--rose-ink);
  border-radius: 99px;
  font-size: 13px;
  font-weight: 500;
  animation: bt-pop .3s var(--ease-back) both;
}
.remove-tag {
  width: 18px;
  height: 18px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  background: rgba(168,106,130,.16);
  color: var(--rose-ink);
  font-size: 14px;
  line-height: 1;
}
.remove-tag:active { transform: scale(.9); }

.avoid-input-row { display: flex; gap: 8px; }
.avoid-input-row input {
  flex: 1;
  min-width: 0;
  padding: 12px 15px;
  border: 1px solid var(--line);
  border-radius: 16px;
  font-size: 14px;
  background: var(--card);
  color: var(--ink);
  outline: none;
  box-shadow: var(--sh-sm);
  transition: border-color var(--t-fast) var(--ease),
    box-shadow var(--t-fast) var(--ease);
}
.avoid-input-row input::placeholder { color: var(--ink-faint); }
.avoid-input-row input:focus {
  border-color: var(--sage);
  box-shadow: 0 0 0 3px rgba(126, 139, 109, .15);
}
.add-btn {
  flex-shrink: 0;
  padding: 0 18px;
  min-height: 44px;
  background: var(--sheet);
  color: var(--ink);
  border: 1px solid var(--line);
  border-radius: 16px;
  font-size: 14px;
  font-weight: 500;
  box-shadow: var(--sh-sm);
  transition: transform var(--t-fast) var(--ease);
}
.add-btn:active { transform: scale(.98); }

/* ── 하단 바 ── */
.input-bar {
  flex-shrink: 0;
  padding: 10px 16px calc(12px + env(safe-area-inset-bottom));
}

.input-placeholder input {
  width: 100%;
  padding: 13px 16px;
  border: 1px solid var(--line);
  border-radius: 16px;
  font-size: 14px;
  background: var(--sheet);
  color: var(--ink-faint);
  outline: none;
}

.go-chat-btn {
  width: 100%;
  padding: 15px;
  background: var(--ink);
  color: var(--canvas);
  border-radius: 99px;
  font-size: 15px;
  font-weight: 600;
  box-shadow: var(--sh-ink);
  animation: bt-pop .4s var(--ease-back) both;
  transition: transform var(--t-fast) var(--ease);
}
.go-chat-btn:active { transform: scale(.98); }

/* ── 데스크톱 ≥900px ── */
@media (min-width: 900px) {
  /* 앱바·본문·하단바를 중앙 정렬된 한 컬럼으로 모은다 */
  .appbar {
    width: 100%;
    max-width: 620px;
    margin: 0 auto;
    padding: 32px 32px 18px;
  }
  .ab-title { font-size: 28px; }

  .chat-body {
    width: 100%;
    max-width: 620px;
    margin: 0 auto;
    padding: 28px 32px 12px;
  }

  .input-bar {
    width: 100%;
    max-width: 620px;
    margin: 0 auto;
    padding: 12px 32px 24px;
  }
}
</style>
