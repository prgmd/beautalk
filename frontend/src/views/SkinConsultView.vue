<script setup>
import { ref, nextTick, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { useProfileStore } from '@/stores/profile'
import { useToastStore } from '@/stores/toast'
import { api } from '@/services/api'
import GlobalSidebar from '@/components/GlobalSidebar.vue'

const router = useRouter()
const profile = useProfileStore()
const toast = useToastStore()

// 저장 시 patchProfile이 전체 페이로드를 보내므로, 기존 고민·기피성분을
// 덮어쓰지 않도록 진입 시 현재 프로필을 먼저 불러와 둔다.
onMounted(() => { if (!profile.loaded) profile.fetchProfile().catch(() => {}) })

// ── 진단 질문 (규칙 기반). LLM 연동은 다음 단계 — 우선 동작하는 UI를 둔다. ──
// 각 보기는 피부 타입 점수를 가산한다: { dry, oily, sensitive, combo }
const QUESTIONS = [
  {
    q: '세안 후 30분쯤 지나면 피부가 어떤가요?',
    options: [
      { label: '당기고 건조해요', score: { dry: 2 } },
      { label: '적당하고 편안해요', score: {} },
      { label: '전체적으로 번들거려요', score: { oily: 2 } },
      { label: 'T존만 번들거려요', score: { combo: 2 } },
    ],
  },
  {
    q: '모공과 피지는 어떤 편인가요?',
    options: [
      { label: '거의 안 보여요', score: { dry: 1 } },
      { label: 'T존 위주로 보여요', score: { combo: 2 } },
      { label: '전체적으로 넓고 피지가 많아요', score: { oily: 2 } },
      { label: '잘 모르겠어요', score: {} },
    ],
  },
  {
    q: '새 화장품을 쓰면 따갑거나 붉어지나요?',
    options: [
      { label: '자주 그래요', score: { sensitive: 3 } },
      { label: '가끔 그래요', score: { sensitive: 1 } },
      { label: '거의 없어요', score: {} },
    ],
  },
  {
    q: '환절기·겨울철 피부는 어떤가요?',
    options: [
      { label: '각질이 일고 가려워요', score: { dry: 2 } },
      { label: '큰 변화 없어요', score: {} },
      { label: '그래도 번들거려요', score: { oily: 1 } },
    ],
  },
]

const SKIN_LABEL = { dry: '건성', oily: '지성', combo: '복합성', sensitive: '민감성' }
const SKIN_DESC = {
  건성: '수분과 유분이 부족하기 쉬워요. 보습 위주의 가벼운 레이어링을 추천해요.',
  지성: '피지 분비가 활발한 편이에요. 산뜻한 제형과 모공 관리에 신경 써보세요.',
  복합성: 'T존은 번들, 볼은 건조한 타입이에요. 부위별로 다르게 케어하면 좋아요.',
  민감성: '외부 자극에 예민한 편이에요. 저자극·진정 성분 위주로 골라보세요.',
}

const messages = ref([
  { id: 1, role: 'ai', text: '안녕하세요! 몇 가지 질문으로 피부 타입을 알아볼게요. 편하게 답해주세요 🌿' },
])
const step = ref(0) // 0..QUESTIONS.length-1, then 'done'
const scores = ref({ dry: 0, oily: 0, sensitive: 0, combo: 0 })
const result = ref('') // 한글 라벨
const saving = ref(false)

const currentQ = computed(() => (step.value < QUESTIONS.length ? QUESTIONS[step.value] : null))
const bodyEl = ref(null)

function scrollToBottom() {
  nextTick(() => { if (bodyEl.value) bodyEl.value.scrollTop = bodyEl.value.scrollHeight })
}

// 첫 질문을 띄운다(진입 직후)
function ensureFirstQuestion() {
  if (messages.value.length === 1) {
    messages.value.push({ id: Date.now(), role: 'ai', text: QUESTIONS[0].q, isQuestion: true })
    scrollToBottom()
  }
}
ensureFirstQuestion()

// 점수 가산 후 다음 질문으로 진행한다(보기/잘모름/자유입력 공통).
function applyScoreAndAdvance(score) {
  for (const [k, v] of Object.entries(score || {})) scores.value[k] += v
  const next = step.value + 1
  scrollToBottom()
  setTimeout(() => {
    if (next < QUESTIONS.length) {
      step.value = next
      messages.value.push({ id: Date.now() + 1, role: 'ai', text: QUESTIONS[next].q, isQuestion: true })
      scrollToBottom()
    } else {
      step.value = next
      finish()
    }
  }, 350)
}

// 보기 클릭
function answer(opt) {
  messages.value.push({ id: Date.now(), role: 'user', text: opt.label })
  applyScoreAndAdvance(opt.score)
}

// '잘 모르겠어요' — 점수 없이 다음으로
function skipQuestion() {
  messages.value.push({ id: Date.now(), role: 'user', text: '잘 모르겠어요' })
  applyScoreAndAdvance({})
}

// 자유 입력 — LLM이 보기 중 가장 가까운 것에 매칭
const freeText = ref('')
const matching = ref(false)
async function submitFreeText() {
  const text = freeText.value.trim()
  if (!text || matching.value || !currentQ.value) return
  const q = currentQ.value
  freeText.value = ''
  messages.value.push({ id: Date.now(), role: 'user', text })
  matching.value = true
  scrollToBottom()
  try {
    const { data } = await api.post('/consult/skin/match/', {
      question: q.q,
      options: q.options.map((o) => o.label),
      text,
    })
    const idx = data?.index ?? -1
    if (idx >= 0 && idx < q.options.length) {
      // 매칭된 보기를 짧게 알려주고 그 점수를 적용
      messages.value.push({ id: Date.now() + 1, role: 'ai', text: `'${q.options[idx].label}'에 가깝게 봤어요.` })
      applyScoreAndAdvance(q.options[idx].score)
    } else {
      // 매칭 실패 — 점수 없이 진행
      messages.value.push({ id: Date.now() + 1, role: 'ai', text: '음, 이 항목은 참고만 할게요. 다음으로 넘어갈게요.' })
      applyScoreAndAdvance({})
    }
  } catch {
    messages.value.push({ id: Date.now() + 1, role: 'ai', text: '지금은 분석이 어려워요. 이 항목은 건너뛸게요.', error: true })
    applyScoreAndAdvance({})
  } finally {
    matching.value = false
  }
}

function determine() {
  const s = scores.value
  if (s.sensitive >= 3) return '민감성'
  const core = { dry: s.dry, oily: s.oily, combo: s.combo }
  const max = Math.max(core.dry, core.oily, core.combo)
  if (max === 0) return s.sensitive > 0 ? '민감성' : '복합성'
  // 동점이거나 combo가 최대면 복합성
  if (core.combo === max) return '복합성'
  if (core.dry === max) return '건성'
  return '지성'
}

function finish() {
  result.value = determine()
  messages.value.push({
    id: Date.now(),
    role: 'ai',
    text: `진단 결과, 회원님의 피부는 '${result.value}'에 가까워요.\n${SKIN_DESC[result.value]}`,
    isResult: true,
  })
  scrollToBottom()
}

async function saveToProfile() {
  if (saving.value || !result.value) return
  saving.value = true
  try {
    await profile.patchProfile({ skinType: result.value })
    toast.success(`피부 타입을 '${result.value}'(으)로 저장했어요`)
    router.push('/home')
  } catch {
    toast.error('저장에 실패했어요. 잠시 후 다시 시도해 주세요.')
    saving.value = false
  }
}

// 한글 IME 조합 중 Enter 무시
function onEnter(e) {
  if (e.isComposing) return
  submitFreeText()
}

function restart() {
  messages.value = [{ id: Date.now(), role: 'ai', text: '다시 진단해 볼게요. 편하게 답해주세요 🌿' }]
  scores.value = { dry: 0, oily: 0, sensitive: 0, combo: 0 }
  step.value = 0
  result.value = ''
  messages.value.push({ id: Date.now() + 1, role: 'ai', text: QUESTIONS[0].q, isQuestion: true })
  scrollToBottom()
}
</script>

<template>
  <div class="screen">
    <div class="main">
      <header class="appbar">
        <button class="back" @click="router.push('/consult')" aria-label="뒤로">‹</button>
        <span class="ab-title serif">피부 타입 진단</span>
        <span class="ab-step">{{ Math.min(step + 1, QUESTIONS.length) }} / {{ QUESTIONS.length }}</span>
      </header>

      <div ref="bodyEl" class="body">
        <div v-for="msg in messages" :key="msg.id" class="msg" :class="msg.role">
          <div v-if="msg.role === 'ai'" class="av">🌿</div>
          <div class="bubble" :class="[msg.role, { result: msg.isResult }]">{{ msg.text }}</div>
        </div>

        <!-- 현재 질문의 보기 -->
        <div v-if="currentQ" class="options">
          <button
            v-for="(o, i) in currentQ.options" :key="i"
            class="option" :disabled="matching" @click="answer(o)"
          >{{ o.label }}</button>
          <button class="option unsure" :disabled="matching" @click="skipQuestion">잘 모르겠어요</button>
        </div>

        <!-- 매칭 중 로딩 -->
        <div v-if="matching" class="msg ai">
          <div class="av">🌿</div>
          <div class="bubble ai loading"><span class="dot" /><span class="dot" /><span class="dot" /></div>
        </div>

        <!-- 결과 액션 -->
        <div v-else-if="result" class="result-actions">
          <button class="ra-primary" :disabled="saving" @click="saveToProfile">
            {{ saving ? '저장 중…' : `'${result}'로 프로필 저장` }}
          </button>
          <button class="ra-ghost" @click="router.push('/chat')">이 타입으로 제품 추천받기 →</button>
          <button class="ra-text" @click="restart">다시 진단하기</button>
        </div>
      </div>

      <!-- 직접 입력 (LLM 매칭) — 질문 단계에서만 -->
      <div v-if="currentQ" class="composer">
        <input
          v-model="freeText"
          placeholder="직접 입력해도 돼요 (예: 겨울엔 각질이 일어나요)"
          :disabled="matching"
          @keydown.enter="onEnter"
        />
        <button class="go" :disabled="!freeText.trim() || matching" aria-label="보내기" @click="submitFreeText">↑</button>
      </div>
    </div>

    <GlobalSidebar />
  </div>
</template>

<style scoped>
.screen { height: 100%; display: flex; flex-direction: column; overflow: hidden; }
.main { flex: 1; min-height: 0; display: flex; flex-direction: column; overflow: hidden; }

.appbar {
  flex-shrink: 0; display: flex; align-items: center; gap: 12px;
  padding: calc(12px + env(safe-area-inset-top)) 18px 12px;
  border-bottom: 1px solid var(--line-soft);
}
.back { font-size: 26px; line-height: 1; color: var(--ink-soft); width: 30px; }
.ab-title { font-size: 17px; font-weight: 600; flex: 1; }
.ab-step { font-size: 13px; color: var(--ink-faint); }

.body { flex: 1; min-height: 0; overflow-y: auto; padding: 20px 18px 28px; display: flex; flex-direction: column; gap: 14px; }

.msg { display: flex; gap: 9px; align-items: flex-end; animation: bt-rise .3s var(--ease) both; }
.msg.user { flex-direction: row-reverse; }
.av {
  width: 30px; height: 30px; border-radius: 50%; flex-shrink: 0;
  background: var(--sage-soft); border: 1px solid var(--line); box-shadow: var(--sh-sm);
  display: flex; align-items: center; justify-content: center; font-size: 14px;
}
.bubble {
  max-width: 80%; font-size: 14.5px; line-height: 1.6; padding: 11px 15px; border-radius: 17px;
  white-space: pre-line;
}
.bubble.ai { background: var(--card); border: 1px solid var(--line-soft); border-bottom-left-radius: 5px; box-shadow: var(--sh-bub); }
.bubble.user { background: var(--ink); color: var(--canvas); border-bottom-right-radius: 5px; box-shadow: var(--sh-ink); }
.bubble.result { background: var(--sage); color: var(--canvas); border: none; box-shadow: var(--sh-md); font-weight: 500; }

.options { display: flex; flex-direction: column; gap: 8px; margin: 4px 0 0 39px; animation: bt-rise .35s var(--ease) both; }
.option {
  text-align: left; padding: 13px 16px; border-radius: 14px;
  background: var(--card); border: 1px solid var(--line); color: var(--ink);
  font-size: 14px; font-weight: 500; box-shadow: var(--sh-sm);
  transition: transform var(--t-fast) var(--ease), border-color var(--t-fast), background var(--t-fast);
}
.option:hover:not(:disabled) { border-color: var(--sage); background: var(--sage-soft); }
.option:active:not(:disabled) { transform: scale(.98); }
.option:disabled { opacity: .5; cursor: default; }
.option.unsure { border-style: dashed; color: var(--ink-faint); background: transparent; box-shadow: none; }
.option.unsure:hover:not(:disabled) { color: var(--ink-soft); border-color: var(--ink-faint); background: transparent; }

/* 매칭 중 로딩 점 */
.bubble.loading { display: flex; gap: 4px; align-items: center; padding: 13px 16px; }
.dot { width: 6px; height: 6px; border-radius: 50%; background: var(--sage); opacity: .5; animation: bt-bounce 1.2s infinite; }
.dot:nth-child(2) { animation-delay: .2s; }
.dot:nth-child(3) { animation-delay: .4s; }

/* 직접 입력 composer */
.composer {
  flex-shrink: 0; display: flex; align-items: center; gap: 9px;
  padding: 8px 16px calc(12px + env(safe-area-inset-bottom));
  border-top: 1px solid var(--line-soft);
}
.composer input {
  flex: 1; border: 1px solid var(--line); background: var(--card); border-radius: 16px;
  padding: 12px 16px; font-size: 14px; outline: none; color: var(--ink); box-shadow: var(--sh-sm);
  transition: border-color var(--t-fast), box-shadow var(--t-fast);
}
.composer input:focus { border-color: var(--sage); box-shadow: 0 0 0 3px rgba(126,139,109,.15); }
.composer input:disabled { opacity: .6; }
.composer input::placeholder { color: var(--ink-faint); }
.composer .go {
  width: 44px; height: 44px; flex-shrink: 0; border-radius: 14px;
  background: var(--ink); color: var(--canvas); font-size: 18px; box-shadow: var(--sh-ink);
  display: flex; align-items: center; justify-content: center;
  transition: transform var(--t) var(--ease), opacity var(--t-fast);
}
.composer .go:disabled { opacity: .3; background: var(--ink-faint); box-shadow: none; }
.composer .go:not(:disabled):active { transform: scale(.94); }

.result-actions { display: flex; flex-direction: column; gap: 9px; margin: 6px 0 0 39px; animation: bt-rise .4s var(--ease) both; }
.ra-primary {
  padding: 14px; border-radius: 99px; background: var(--ink); color: var(--canvas);
  font-size: 14.5px; font-weight: 700; box-shadow: var(--sh-ink);
  transition: transform var(--t-fast) var(--ease), opacity var(--t-fast);
}
.ra-primary:not(:disabled):active { transform: scale(.98); }
.ra-primary:disabled { opacity: .5; }
.ra-ghost {
  padding: 13px; border-radius: 99px; background: var(--card); border: 1px solid var(--line);
  font-size: 13.5px; font-weight: 600; color: var(--ink); box-shadow: var(--sh-sm);
}
.ra-text { padding: 8px; font-size: 13px; color: var(--ink-faint); font-weight: 600; }
.ra-text:hover { color: var(--ink-soft); }

@media (min-width: 900px) {
  .screen { flex-direction: row; }
  .appbar, .body, .composer { width: 100%; max-width: 640px; margin: 0 auto; }
  .appbar { padding-left: 40px; padding-right: 40px; }
  .body { padding-left: 40px; padding-right: 40px; }
  .composer { padding-left: 40px; padding-right: 40px; padding-bottom: 22px; }
}
</style>
