<script setup>
import { ref, computed, watch, nextTick, onMounted, onUnmounted } from 'vue'
import { useChatStore } from '@/stores/chat'
import { useLikesStore } from '@/stores/likes'
import { useProductDetailStore } from '@/stores/productDetail'
import { useConfirmStore } from '@/stores/confirm'
import { useAuthStore } from '@/stores/auth'
import { usePaywallStore } from '@/stores/paywall'
import GlobalSidebar from '@/components/GlobalSidebar.vue'
import DewyLoader from '@/components/DewyLoader.vue'
import Icon from '@/components/Icon.vue'
import { FORM_OPTIONS, PRICE_BANDS, formLabel } from '@/utils/forms'
import { api } from '@/services/api'

const chat = useChatStore()
const likes = useLikesStore()
const productDetail = useProductDetailStore()
const confirm = useConfirmStore()
const paywall = usePaywallStore()

const inputText = ref('')
const chatBody = ref(null)

const isEmpty = computed(() => chat.messages.length === 0)

// 오늘 남은 대화 횟수 (서버 기준). 초기 로드 시 한 번 조회.
const remaining = computed(() => chat.quota?.remaining ?? null)
const isDepleted = computed(() => remaining.value === 0)
const quotaNotice = computed(() => {
  if (remaining.value == null) return ''
  return isDepleted.value
    ? '오늘의 무료 대화가 소진됐어요.'
    : `오늘의 무료 대화가 ${remaining.value}번 남았어요.`
})
onMounted(() => chat.fetchQuota())

// ── 날씨 (배경 + 뱃지 + 빈 화면 인사) ──
const authStore = useAuthStore()
const weather = ref({ condition: 'default', temp: null, desc: '' })

const WX_ICON  = { clear: '☀️', rain: '🌧️', snow: '❄️', clouds: '☁️', default: '🌿' }
const wxIcon   = computed(() => WX_ICON[weather.value.condition] || WX_ICON.default)

// 날씨 수동 선택 시트
const WX_OPTIONS = [
  { key: 'clear',  icon: '☀️', label: '맑음' },
  { key: 'clouds', icon: '☁️', label: '흐림' },
  { key: 'rain',   icon: '🌧️', label: '비' },
  { key: 'snow',   icon: '❄️', label: '눈' },
]
const showWeatherPicker = ref(false)
function pickWeather(key) {
  weather.value = { ...weather.value, condition: key }
  showWeatherPicker.value = false
}
// 드롭다운 바깥 클릭 시 닫기 (열려있을 때만 처리)
function closeWeatherPicker() {
  if (showWeatherPicker.value) showWeatherPicker.value = false
}
onMounted(() => document.addEventListener('click', closeWeatherPicker))
onUnmounted(() => document.removeEventListener('click', closeWeatherPicker))

const userName = computed(() => {
  const u = authStore.user
  if (!u) return ''
  if (u.nickname) return u.nickname
  if (u.email) return u.email.split('@')[0]
  return ''
})

const WX_SUGGEST = {
  clear:  '맑고 자외선이 강한 날이에요. 선크림을 꼭 챙겨보는 건 어떨까요?',
  rain:   '비가 내리고 있어요. 워터프루프 제품을 챙겨보는 건 어떨까요?',
  snow:   '춥고 건조한 날씨예요. 보습 크림으로 피부를 지켜보는 건 어떨까요?',
  clouds: '흐린 날인만큼 자외선 차단을 신경 써보는 건 어떨까요?',
}
const wxWeatherLines = computed(() => {
  const { condition, temp, desc } = weather.value
  if (temp == null) return null
  return {
    line1: `오늘 서울 날씨는 ${desc} ${temp}°C예요.`,
    line2: WX_SUGGEST[condition] || '',
  }
})

async function fetchWeather() {
  try {
    const { data } = await api.get('/weather/', { auth: false })
    if (data?.condition) weather.value = data
  } catch {
    // WEATHER_API_KEY 미설정이거나 API 오류면 조용히 무시 (기본 문구 유지)
  }
}
onMounted(fetchWeather)

async function sendMessage(text) {
  const msg = text || inputText.value.trim()
  if (!msg || chat.isLoading) return

  // 첫 메시지이고 사전 조건을 골랐다면, 봇 인사말을 먼저 심어 조건을 확인시킨다.
  // (history에 포함되어 대화·추천 단계 모두 이 조건을 인지)
  if (isEmpty.value && conditionGreeting.value) {
    chat.seedAssistant(conditionGreeting.value)
  }

  // 사용량 제한은 백엔드 throttle(100/day)이 단일 기준. 초과 시 서버가 429를 주면
  // api.js가 페이월을 띄운다(프론트는 별도 카운팅하지 않는다).
  inputText.value = ''
  await chat.sendChat(msg)
}

// 한글 등 IME 조합 중의 Enter는 무시한다.
function onEnterKey(e) {
  if (e.isComposing) return
  sendMessage()
}

// ── 추천 조건(제형·가격대) ──
const showFilters = ref(false)
const selForms = ref([]) // 제형 키(복수)
const selBand = ref(null) // 가격대 키(단일)

const activeCount = computed(() => selForms.value.length + (selBand.value ? 1 : 0))

function toggleForm(key) {
  const i = selForms.value.indexOf(key)
  if (i === -1) selForms.value.push(key)
  else selForms.value.splice(i, 1)
}
function toggleBand(key) {
  selBand.value = selBand.value === key ? null : key
}
function clearFilters() {
  selForms.value = []
  selBand.value = null
}

// 선택한 조건 요약(버튼 옆에 표시)
const filterSummary = computed(() => {
  const parts = selForms.value.map(formLabel)
  const band = PRICE_BANDS.find((b) => b.key === selBand.value)
  if (band) parts.push(band.label)
  return parts.join(' · ')
})

// 사전 선택 조건 → 첫 봇 인사말. 아무것도 안 골랐으면 빈 문자열(인사말 생략).
const conditionGreeting = computed(() => {
  if (!activeCount.value) return ''
  const quoted = []
  selForms.value.forEach((k) => quoted.push(`'${formLabel(k)}'`))
  const band = PRICE_BANDS.find((b) => b.key === selBand.value)
  if (band) quoted.push(`'${band.label}'`)
  return `사전에 ${quoted.join(', ')} 조건을 고르셨네요! 어떤 피부 고민이 있으신지 편하게 말씀해 주시면 딱 맞는 제품을 찾아드릴게요.`
})

// 사전 선택 조건 → 사용자 발화 프롬프트. '대화 바로 시작하기'가 이 문장을 전송한다.
const conditionPrompt = computed(() => {
  const forms = selForms.value.map(formLabel)
  const band = PRICE_BANDS.find((b) => b.key === selBand.value)
  if (forms.length && band) return `${forms.join(', ')} 제품을 ${band.label} 가격대로 추천받고 싶어요.`
  if (forms.length) return `${forms.join(', ')} 제품을 추천받고 싶어요.`
  if (band) return `${band.label} 가격대의 제품을 추천받고 싶어요.`
  return ''
})

// 선택값 → 백엔드 filters. 아무것도 안 골랐으면 undefined(=기존 동작).
function buildFilters() {
  const f = {}
  if (selForms.value.length) f.forms = [...selForms.value]
  const band = PRICE_BANDS.find((b) => b.key === selBand.value)
  if (band) {
    if (band.min != null) f.price_min = band.min
    if (band.max != null) f.price_max = band.max
  }
  return Object.keys(f).length ? f : undefined
}

async function getRecommendations() {
  // 아직 준비(ready)되지 않았으면 정보 부족을 알리고 동의를 받은 뒤에만 진행한다.
  if (!chat.ready && !(await confirm.ask({
    title: '아직 충분한 정보가 모이지 않았어요',
    message: '그래도 추천해드릴까요?',
    confirmText: '추천받기',
  }))) return
  chat.requestRecommend(buildFilters())
}

// 사전 조건만 고르고 입력 없이 대화 시작 — 조건을 발화로 만들어 그대로 전송한다.
// (sendMessage 대신 직접 sendChat: 인사말 중복 심기를 피하고 바로 사용자 발화로 시작)
function startChatWithConditions() {
  if (!conditionPrompt.value || chat.isLoading) return
  inputText.value = ''
  chat.sendChat(conditionPrompt.value)
}

async function newChat() {
  if (chat.messages.length && !(await confirm.ask({
    title: '새 대화를 시작할까요?',
    message: '지금까지의 대화 내용이 모두 지워져요.',
    confirmText: '새 대화', danger: true,
  }))) return
  chat.clearMessages()
}

function scrollToBottom() {
  if (chatBody.value) chatBody.value.scrollTop = chatBody.value.scrollHeight
}

watch(
  () => [chat.messages.length, chat.isLoading],
  () => nextTick(scrollToBottom),
)

function formatPrice(n) {
  return n != null ? n.toLocaleString('ko-KR') + '원' : '가격 정보 없음'
}
</script>

<template>
  <div class="screen" :class="'wx-' + weather.condition">
    <div class="main">
    <!-- 앱바 -->
    <header class="appbar">
      <button class="ab-brand serif" @click="$router.push('/home')" aria-label="홈으로">beau<span class="it">talk</span></button>
      <div class="ab-right">
        <!-- 날씨 드롭다운 -->
        <div class="wx-dropdown">
          <button
            class="wx-badge" :class="{ open: showWeatherPicker }"
            @click.stop="showWeatherPicker = !showWeatherPicker" title="날씨 바꾸기"
          >
            {{ wxIcon }}<span v-if="weather.temp != null"> {{ weather.temp }}°C</span><span class="wx-cycle">▾</span>
          </button>
          <Transition name="wxdrop">
            <div v-if="showWeatherPicker" class="wx-menu">
              <button
                v-for="o in WX_OPTIONS" :key="o.key"
                class="wx-menu-item" :class="{ on: weather.condition === o.key }"
                @click="pickWeather(o.key)"
              >
                <span class="wmi-icon">{{ o.icon }}</span>
                <span class="wmi-label">{{ o.label }}</span>
              </button>
            </div>
          </Transition>
        </div>
        <!-- 프리미엄: 무제한 뱃지 / 무료: 남은 대화 횟수 → 클릭 시 요금제(결제창) -->
        <button
          v-if="authStore.isPremium"
          class="quota-chip premium"
          @click="paywall.open()" title="요금제 보기"
        >✨ 프리미엄</button>
        <button
          v-else-if="remaining != null"
          class="quota-chip" :class="{ low: remaining <= 10 }"
          @click="paywall.open()" title="요금제 보기"
        >
          <Icon name="chat" :size="12" /> 남은 대화 <strong>{{ remaining }}</strong>회
        </button>
        <button v-if="!isEmpty" class="ab-new" @click="newChat"><span class="abn-ic">⟲</span> 새 대화</button>
      </div>
    </header>

    <!-- 추천 결과 화면 -->
    <div v-if="chat.mode === 'result'" class="body result">
      <!-- 로딩 -->
      <div v-if="chat.isRecommending" class="result-loading">
        <DewyLoader
          text="대화 내역으로 고르는 중"
          subtitle="맑은 피부에 어울리는 제품을 찾고 있어요"
          :size="150"
        />
      </div>

      <!-- 에러 -->
      <div v-else-if="chat.recommendError" class="result-error">
        <p class="err-icon">🌿</p>
        <p class="err-text">{{ chat.recommendError }}</p>
        <div class="err-actions">
          <button class="ghost-btn" @click="chat.backToChat()">대화로 돌아가기</button>
          <button class="primary-btn" @click="getRecommendations()">다시 시도</button>
        </div>
      </div>

      <!-- 결과 -->
      <template v-else-if="chat.recommendBatch">
        <!-- 완화 안내: 조건이 부족해 일부 풀었을 때 -->
        <div v-if="chat.recommendBatch.constraints?.relaxed" class="relax-banner">
          <span class="rb-ic"><Icon name="info" :size="14" /></span>{{ chat.recommendBatch.constraints.note }}
        </div>

        <div class="result-head">
          <p class="result-summary serif">{{ chat.recommendBatch.content }}</p>
        </div>

        <div class="rec-list">
          <article v-for="(product, index) in chat.recommendBatch.products" :key="product.id" class="rec-card" :style="{ '--d': index * 40 + 'ms' }">
            <div class="rec-arch" @click="productDetail.open(product)">
              <img v-if="product.image" :src="product.image" :alt="product.name" />
              <Icon v-else name="leaf" :size="38" class="rec-ph" />
              <button
                class="rec-heart"
                :class="{ liked: likes.isLiked(product.id) }"
                :aria-label="likes.isLiked(product.id) ? '찜 해제' : '찜하기'"
                :aria-pressed="likes.isLiked(product.id)"
                @click.stop="likes.toggleLike(product)"
              ><Icon :name="likes.isLiked(product.id) ? 'heart-fill' : 'heart'" :size="16" /></button>
            </div>
            <div
              class="rec-meta" role="button" tabindex="0"
              @click="productDetail.open(product)"
              @keydown.enter.prevent="productDetail.open(product)"
              @keydown.space.prevent="productDetail.open(product)"
            >
              <p class="rec-brand">{{ product.brand }}</p>
              <p class="rec-name">{{ product.name }}</p>
              <p class="rec-price serif">{{ formatPrice(product.price) }}</p>
            </div>

            <!-- 제형 + 제약 충족 배지 -->
            <div v-if="product.form?.length || product.meets" class="rec-badges">
              <span v-for="fk in product.form" :key="fk" class="badge form">{{ formLabel(fk) }}</span>
              <span
                v-if="product.meets && 'price' in product.meets"
                class="badge" :class="product.meets.price ? 'ok' : 'no'"
              >가격 {{ product.meets.price ? '✓' : '✗' }}</span>
              <span
                v-if="product.meets && 'form' in product.meets"
                class="badge" :class="product.meets.form ? 'ok' : 'no'"
              >제형 {{ product.meets.form ? '✓' : '✗' }}</span>
            </div>

            <p v-if="product.reason" class="rec-reason">{{ product.reason }}</p>
            <a
              v-if="product.oliveyoungUrl && product.oliveyoungUrl !== '#'"
              :href="product.oliveyoungUrl" target="_blank" rel="noopener noreferrer" class="rec-link"
            >올리브영에서 보기 <Icon name="external" :size="14" /></a>
          </article>
        </div>

        <button class="more-chat-btn" @click="chat.backToChat()">← 조금 더 대화할래요</button>
      </template>
    </div>

    <!-- 대화 화면 -->
    <template v-else>
      <div ref="chatBody" class="body chat">
        <!-- 빈 상태 -->
        <div v-if="isEmpty" class="empty">
          <div class="empty-orb">
            <DewyLoader :size="96" />
          </div>
          <h1 class="empty-title serif">
            <template v-if="userName">{{ userName }}님<br><em>안녕하세요!</em></template>
            <template v-else>맑게 비치는<br><em>당신의 피부</em></template>
          </h1>
          <div v-if="wxWeatherLines" class="empty-weather">
            <p class="ew-line1">{{ wxWeatherLines.line1 }}</p>
            <p class="ew-line2">{{ wxWeatherLines.line2 }}</p>
          </div>
          <p class="empty-desc" v-else>피부 고민을 편하게 적어주세요. 저장된 프로필을 참고해 맞춤 추천을 드려요.</p>
        </div>

        <!-- 메시지 -->
        <template v-else>
          <div v-for="msg in chat.messages" :key="msg.id" class="msg" :class="msg.role">
            <div v-if="msg.role === 'assistant'" class="av">🌿</div>
            <div class="bubble-wrap">
              <div class="bubble" :class="[msg.role, { error: msg.error }]">{{ msg.text }}</div>
              <button
                v-if="msg.error && msg.id === chat.messages.at(-1)?.id"
                class="retry-btn"
                @click="chat.retryChat()"
              >다시 시도</button>
            </div>
          </div>

          <!-- 로딩 -->
          <div v-if="chat.isLoading" class="msg assistant">
            <div class="av">🌿</div>
            <div class="bubble assistant loading">
              <span class="dot" /><span class="dot" /><span class="dot" />
            </div>
          </div>
        </template>
      </div>

      <!-- 추천받기 -->
      <div class="reco-bar">
        <!-- 조건 좁히기 — 대화 시작 전(빈 화면)에만 -->
        <template v-if="isEmpty">
          <button class="filters-toggle" :class="{ open: showFilters, active: activeCount }" @click="showFilters = !showFilters">
            <span class="ft-ic">⛃</span>
            <span class="ft-text">조건 좁히기 <span class="opt">선택</span></span>
            <span v-if="activeCount" class="cnt">{{ activeCount }}</span>
            <span class="chev">{{ showFilters ? '▾' : '▸' }}</span>
          </button>

          <div v-if="showFilters" class="filters-panel">
            <div class="f-group">
              <span class="f-label">제형</span>
              <div class="chips">
                <button
                  v-for="o in FORM_OPTIONS" :key="o.key"
                  class="chip" :class="{ on: selForms.includes(o.key) }"
                  @click="toggleForm(o.key)"
                >{{ o.label }}</button>
              </div>
            </div>
            <div class="f-group">
              <span class="f-label">가격대</span>
              <div class="chips">
                <button
                  v-for="b in PRICE_BANDS" :key="b.key"
                  class="chip" :class="{ on: selBand === b.key }"
                  @click="toggleBand(b.key)"
                >{{ b.label }}</button>
              </div>
            </div>
            <div v-if="activeCount" class="filters-actions">
              <button class="fa-clear" @click="clearFilters">전체 해제</button>
              <button class="fa-start" @click="startChatWithConditions">대화 바로 시작하기</button>
            </div>
          </div>

          <!-- 접었을 때도 선택한 조건을 보이게 -->
          <p v-if="!showFilters && filterSummary" class="filter-summary">적용: {{ filterSummary }}</p>
        </template>

        <!-- 대화 시작 후 — 적용 조건 요약(읽기 전용) + 추천 버튼 -->
        <template v-else>
          <p v-if="filterSummary" class="filter-summary locked">선택한 조건: {{ filterSummary }}</p>
          <button class="reco-btn" :class="{ ready: chat.ready }" @click="getRecommendations()">
            <span class="lf"><Icon name="sparkle" :size="16" /></span> 추천 3개 받기{{ chat.ready ? ' · 준비됐어요' : '' }}
          </button>
        </template>
      </div>

      <!-- 남은 대화 안내 (프리미엄은 무제한이라 생략) -->
      <p
        v-if="quotaNotice && !authStore.isPremium"
        class="quota-notice" :class="{ depleted: isDepleted }"
        @click="isDepleted && paywall.open()"
      >{{ quotaNotice }}<span v-if="isDepleted" class="qn-cta"> 프리미엄 보기 →</span></p>

      <!-- 입력 -->
      <div class="composer">
        <input
          v-model="inputText"
          placeholder="피부 고민을 적어주세요"
          :disabled="chat.isLoading"
          @keydown.enter="onEnterKey"
        />
        <button class="go" :disabled="!inputText.trim() || chat.isLoading" aria-label="보내기" @click="sendMessage()">↑</button>
      </div>
    </template>
    </div>

    <GlobalSidebar />
  </div>
</template>

<style scoped>
.screen { height: 100%; display: flex; flex-direction: column; overflow: hidden; }
.main { flex: 1; min-height: 0; display: flex; flex-direction: column; overflow: hidden; }

/* 앱바 */
.appbar {
  flex-shrink: 0;
  display: flex; align-items: center; justify-content: space-between;
  padding: calc(10px + env(safe-area-inset-top)) 20px 12px;
}
.ab-brand { font-size: 21px; font-weight: 500; letter-spacing: -.3px; }
.ab-brand .it { font-style: italic; color: var(--sage); }
.ab-right { display: flex; align-items: center; gap: 8px; margin-left: auto; }
.quota-chip {
  display: inline-flex; align-items: center; gap: 4px;
  font-size: 12px; color: var(--ink-soft); font-weight: 500;
  padding: 4px 11px; border-radius: 99px;
  background: var(--sage-soft); border: 1px solid var(--line-soft);
  cursor: pointer; transition: border-color var(--t-fast), color var(--t-fast);
}
.quota-chip strong { font-weight: 700; color: var(--sage-ink); }
.quota-chip:hover { border-color: var(--sage); color: var(--ink); }
.quota-chip:active { transform: scale(.96); }
.quota-chip.low { background: var(--danger-bg); border-color: var(--danger-border); }
.quota-chip.low strong { color: var(--danger); }
.quota-chip.premium {
  background: var(--ink); color: var(--canvas); border-color: transparent;
  font-weight: 700; box-shadow: var(--sh-ink);
}
.quota-chip.premium:hover { color: var(--canvas); }
.wx-badge {
  display: inline-flex; align-items: center; gap: 3px;
  font-size: 12px; color: var(--ink-faint); font-weight: 500;
  padding: 4px 10px; border-radius: 99px;
  background: var(--sheet); border: 1px solid var(--line-soft);
  cursor: pointer; transition: border-color var(--t-fast), color var(--t-fast);
}
.wx-badge:hover { border-color: var(--sage); color: var(--ink); }
.wx-badge:active { transform: scale(.96); }
.wx-cycle { font-size: 11px; color: var(--ink-faint); margin-left: 1px; }
.ab-new {
  display: inline-flex; align-items: center; gap: 6px;
  padding: 8px 14px; border-radius: 99px;
  border: 1px solid var(--line); background: var(--sheet); color: var(--ink-soft);
  font-size: 13px; font-weight: 600; box-shadow: var(--sh-sm);
  transition: transform var(--t) var(--ease), color var(--t-fast), border-color var(--t-fast);
}
.ab-new .abn-ic { font-size: 15px; }
.ab-new:hover { color: var(--ink); border-color: var(--ink-faint); }
.ab-new:active { transform: scale(.97); }

.body { flex: 1; min-height: 0; overflow-y: auto; }

/* ── 빈 상태 ── */
.chat { padding: 4px 20px 12px; }
.empty {
  min-height: 100%;
  display: flex; flex-direction: column; align-items: center; justify-content: center;
  text-align: center; padding: 20px 8px 40px; gap: 14px;
}
.empty-orb { margin-bottom: 4px; }
.empty-weather { display: flex; flex-direction: column; gap: 4px; text-align: center; }
.ew-line1 { font-size: 13.5px; color: var(--ink-soft); }
.ew-line2 { font-size: 13px; color: var(--ink-faint); }
.empty-title { font-size: 26px; font-weight: 400; line-height: 1.25; letter-spacing: -.3px; }
.empty-title em { font-style: italic; }
.empty-desc { font-size: 13.5px; color: var(--ink-soft); line-height: 1.7; max-width: 300px; }

/* ── 메시지 ── */
.msg { display: flex; gap: 9px; margin-bottom: 14px; align-items: flex-end; animation: bt-rise .35s var(--ease) both; }
.msg.user { flex-direction: row-reverse; }
.av {
  width: 30px; height: 30px; border-radius: 50%; flex-shrink: 0;
  background: var(--sage-soft); border: 1px solid var(--line); box-shadow: var(--sh-sm);
  display: flex; align-items: center; justify-content: center; font-size: 14px;
}
.bubble-wrap { display: flex; flex-direction: column; gap: 7px; max-width: 80%; }
.msg.user .bubble-wrap { align-items: flex-end; }
.bubble {
  font-size: 14.5px; line-height: 1.6; padding: 11px 15px; border-radius: 17px; white-space: pre-wrap;
}
.bubble.assistant { background: var(--card); border: 1px solid var(--line-soft); border-bottom-left-radius: 5px; box-shadow: var(--sh-bub); }
.bubble.user { background: var(--ink); color: var(--canvas); border-bottom-right-radius: 5px; box-shadow: var(--sh-ink); }
.bubble.error { background: var(--danger-bg); color: var(--danger); border-color: var(--danger-border); }
.retry-btn {
  align-self: flex-start; padding: 6px 14px; border-radius: 99px;
  border: 1px solid var(--line); background: var(--sheet); font-size: 12.5px; box-shadow: var(--sh-sm);
}
.bubble.loading { display: flex; gap: 4px; align-items: center; padding: 13px 16px; }
.dot { width: 6px; height: 6px; border-radius: 50%; background: var(--sage); opacity: .5; animation: bt-bounce 1.2s infinite; }
.dot:nth-child(2) { animation-delay: .2s; }
.dot:nth-child(3) { animation-delay: .4s; }

/* ── 추천 조건 패널 ── */
.reco-bar { flex-shrink: 0; padding: 8px 20px 4px; }
.filters-toggle {
  width: 100%; display: flex; align-items: center; gap: 8px;
  padding: 10px 13px; margin-bottom: 8px; font-size: 13px; font-weight: 600; color: var(--ink-soft);
  background: var(--card); border: 1px solid var(--line); border-radius: 99px; box-shadow: var(--sh-sm);
  transition: border-color var(--t-fast), color var(--t-fast);
}
.filters-toggle:hover { color: var(--ink); border-color: var(--ink-faint); }
.filters-toggle.active { border-color: var(--sage); color: var(--ink); }
.filters-toggle .ft-ic { font-size: 13px; color: var(--sage); }
.filters-toggle .ft-text { flex: 1; text-align: left; }
.filters-toggle .opt { font-weight: 500; color: var(--ink-faint); margin-left: 2px; }
.filters-toggle .cnt {
  display: inline-flex; align-items: center; justify-content: center; min-width: 18px; height: 18px;
  padding: 0 5px; border-radius: 99px; background: var(--sage); color: #fff; font-size: 11px; font-weight: 700;
}
.filters-toggle .chev { color: var(--ink-faint); font-size: 11px; }
.filters-actions {
  display: flex; justify-content: flex-end; align-items: center; gap: 8px;
  margin-top: 4px;
}
.fa-clear {
  padding: 10px 16px; border-radius: 99px;
  font-size: 13px; font-weight: 600; color: var(--ink-soft);
  background: var(--card); border: 1px solid var(--line);
  transition: color var(--t-fast), border-color var(--t-fast);
}
.fa-clear:hover { color: var(--danger); border-color: var(--danger-border); }
.fa-start {
  padding: 10px 18px; border-radius: 99px;
  font-size: 13.5px; font-weight: 700; color: var(--canvas);
  background: var(--ink); border: 1px solid var(--ink); box-shadow: var(--sh-ink);
  transition: transform var(--t) var(--ease);
}
.fa-start:active { transform: scale(.97); }
.filter-summary {
  margin: 0 4px 8px; font-size: 12px; color: var(--sage-ink); font-weight: 600;
}
.filter-summary.locked {
  display: inline-block; padding: 5px 12px; border-radius: 99px;
  background: var(--sage-soft); border: 1px solid var(--line-soft);
}
.filters-panel {
  display: flex; flex-direction: column; gap: 12px;
  padding: 12px 12px 14px; margin-bottom: 8px;
  background: var(--sheet); border: 1px solid var(--line-soft); border-radius: var(--radius);
  animation: bt-rise .25s var(--ease) both;
}
.f-group { display: flex; flex-direction: column; gap: 8px; }
.f-label { font-size: 10px; letter-spacing: 2px; text-transform: uppercase; color: var(--ink-faint); font-weight: 600; }
.chips { display: flex; flex-wrap: wrap; gap: 7px; }
.chip {
  padding: 7px 13px; border-radius: 99px; font-size: 12.5px; font-weight: 500;
  color: var(--ink-soft); background: var(--card); border: 1px solid var(--line); transition: all var(--t-fast);
}
.chip:active { transform: scale(.97); }
.chip.on { background: var(--ink); color: var(--canvas); border-color: var(--ink); box-shadow: var(--sh-sm); }
.reco-btn {
  width: 100%; display: inline-flex; align-items: center; justify-content: center; gap: 8px;
  border: 1px solid var(--ink); background: var(--card); color: var(--ink);
  font-weight: 600; font-size: 14px; padding: 13px; border-radius: 99px; box-shadow: var(--sh-sm);
  transition: transform var(--t) var(--ease), background var(--t-fast), color var(--t-fast);
}
.reco-btn .lf { color: var(--sage); }
.reco-btn:active { transform: scale(.99); }
.reco-btn.ready {
  background: var(--ink); color: var(--canvas); border-color: var(--ink); box-shadow: var(--sh-ink);
}
.reco-btn.ready .lf { color: var(--sage-soft); }

/* 남은 대화 안내 */
.quota-notice {
  flex-shrink: 0; text-align: center; font-size: 11.5px; color: var(--ink-faint);
  padding: 2px 16px 0;
}
.quota-notice.depleted { color: var(--danger); font-weight: 600; cursor: pointer; }
.quota-notice .qn-cta { color: var(--sage-ink); font-weight: 700; }

/* ── 입력 ── */
.composer {
  flex-shrink: 0; display: flex; align-items: center; gap: 9px;
  padding: 8px 16px 10px;
}
.composer input {
  flex: 1; border: 1px solid var(--line); background: var(--card); border-radius: 16px;
  padding: 12px 16px; font-size: 14.5px; outline: none; color: var(--ink); box-shadow: var(--sh-sm);
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

/* ── 추천 결과 ── */
.result { padding: 8px 20px 24px; }
.result-loading { min-height: 70%; display: flex; align-items: center; justify-content: center; }
.result-error {
  min-height: 60%; display: flex; flex-direction: column; align-items: center; justify-content: center;
  text-align: center; gap: 10px;
}
.err-icon { font-size: 34px; }
.err-text { font-size: 14px; color: var(--ink-soft); }
.err-actions { display: flex; gap: 8px; margin-top: 8px; }

/* 완화 안내 배너 */
.relax-banner {
  display: flex; align-items: flex-start; gap: 7px;
  margin: 4px 0 14px; padding: 11px 14px; border-radius: var(--radius);
  background: var(--rose-soft); color: var(--rose-ink);
  font-size: 12.5px; line-height: 1.55; animation: bt-rise .35s var(--ease) both;
}
.relax-banner .rb-ic { flex-shrink: 0; font-size: 13px; }

/* 제형·충족 배지 */
.rec-badges { display: flex; flex-wrap: wrap; gap: 6px; margin: 10px 6px 0; }
.badge {
  font-size: 11px; font-weight: 600; padding: 4px 9px; border-radius: 99px;
  background: var(--panel); color: var(--ink-soft);
}
.badge.form { background: var(--sage-soft); color: var(--sage-ink); }
.badge.ok { background: var(--sage-soft); color: var(--sage-ink); }
.badge.no { background: var(--danger-bg); color: var(--danger); }

.result-head { margin: 6px 2px 18px; animation: bt-rise .4s var(--ease) both; }
.result-summary { font-size: 19px; font-weight: 400; line-height: 1.4; margin-top: 8px; }

.rec-list { display: flex; flex-direction: column; gap: 16px; }
.rec-card {
  background: var(--card); border: 1px solid var(--line-soft); border-radius: var(--radius-lg);
  padding: 12px; box-shadow: var(--sh-soft);
  animation: card-in .5s var(--ease) both; animation-delay: var(--d, 0ms);
  transition: transform var(--t) var(--ease), box-shadow var(--t) var(--ease);
}
.rec-card:hover { transform: translateY(-4px); box-shadow: var(--sh-hover); }
.rec-arch {
  position: relative; aspect-ratio: 16/10; border-radius: 90px 90px 12px 12px; overflow: hidden;
  background: linear-gradient(170deg,#EFE7DB,#E6E3D0 60%,#DEE7DF); cursor: pointer;
  display: flex; align-items: center; justify-content: center;
}
.rec-arch img { width: 100%; height: 100%; object-fit: cover; transition: transform .6s var(--ease); }
.rec-card:hover .rec-arch img { transform: scale(1.06); }
.rec-ph { color: var(--sage); opacity: .5; }
.rec-heart {
  position: absolute; top: 10px; right: 10px; width: 34px; height: 34px; border-radius: 50%;
  background: rgba(28,22,16,.42); border: 1px solid rgba(255,255,255,.35);
  box-shadow: 0 2px 8px rgba(0,0,0,.28); backdrop-filter: blur(2px);
  -webkit-backdrop-filter: blur(2px); font-size: 15px; color: #fff;
  display: flex; align-items: center; justify-content: center;
}
.rec-heart.liked { background: var(--rose); border-color: transparent; color: #fff; }
.rec-meta { padding: 12px 6px 0; cursor: pointer; }
.rec-brand { font-size: 10.5px; letter-spacing: 1.2px; text-transform: uppercase; color: var(--ink-faint); }
.rec-name { font-size: 15px; font-weight: 600; line-height: 1.35; margin: 4px 0 6px; }
.rec-price { font-size: 16px; }
.rec-reason {
  font-size: 12.5px; line-height: 1.6; color: var(--ink-soft);
  background: var(--panel); border-radius: 12px; padding: 11px 13px; margin: 12px 6px 0;
}
.rec-link {
  display: flex; align-items: center; justify-content: center; gap: 6px;
  margin: 12px 6px 4px; padding: 10px;
  border: 1px solid var(--line); border-radius: 12px; font-size: 13px; font-weight: 500; color: var(--ink);
  transition: background var(--t-fast), border-color var(--t-fast);
}
.rec-link:hover { background: var(--sheet); border-color: var(--ink-faint); }

.more-chat-btn {
  display: block; margin: 24px auto 8px; padding: 11px 22px; border-radius: 99px;
  border: 1px solid var(--line); background: var(--sheet); font-size: 13.5px; box-shadow: var(--sh-sm);
}
.ghost-btn { padding: 10px 18px; border-radius: 99px; border: 1px solid var(--line); background: var(--sheet); font-size: 13px; }
.primary-btn { padding: 10px 18px; border-radius: 99px; border: none; background: var(--ink); color: var(--canvas); font-size: 13px; font-weight: 600; box-shadow: var(--sh-ink); }

@keyframes card-in { from { opacity: 0; transform: translateY(12px); } to { opacity: 1; transform: none; } }
@media (prefers-reduced-motion: reduce) {
  .rec-card { animation: none; }
  .rec-card:hover .rec-arch img { transform: none; }
}

/* ── 날씨 드롭다운 ── */
.wx-dropdown { position: relative; }
.wx-badge.open { border-color: var(--sage); color: var(--ink); }
.wx-badge.open .wx-cycle { transform: rotate(180deg); }
.wx-cycle { transition: transform var(--t-fast) var(--ease); }
.wx-menu {
  position: absolute; top: calc(100% + 6px); left: 0; z-index: 50;
  min-width: 132px; padding: 6px;
  background: var(--card); border: 1px solid var(--line-soft);
  border-radius: var(--radius); box-shadow: var(--sh-lg);
  transform-origin: top left;
}
.wx-menu-item {
  width: 100%; display: flex; align-items: center; gap: 9px;
  padding: 9px 11px; border-radius: var(--radius-sm);
  font-size: 13px; color: var(--ink-soft);
  transition: background var(--t-fast);
}
.wx-menu-item:hover { background: var(--panel); }
.wx-menu-item.on { background: var(--sage-soft); color: var(--sage-ink); font-weight: 600; }
.wmi-icon { font-size: 18px; line-height: 1; }
.wmi-label { font-weight: 500; }

/* 펼침 모션 */
.wxdrop-enter-active { transition: opacity var(--t-fast) var(--ease), transform var(--t) var(--ease-back); }
.wxdrop-leave-active { transition: opacity var(--t-fast) var(--ease), transform var(--t-fast) var(--ease); }
.wxdrop-enter-from, .wxdrop-leave-to { opacity: 0; transform: scale(0.9) translateY(-6px); }

/* ── 데스크탑(≥900px) ── */
@media (min-width: 900px) {
  .screen { flex-direction: row; }
  .appbar { max-width: 900px; width: 100%; margin: 0 auto; padding: 22px 40px 10px; }
  .ab-brand { display: none; }
  .chat, .result { max-width: 900px; width: 100%; margin: 0 auto; padding-left: 40px; padding-right: 40px; }
  .reco-bar, .composer { max-width: 900px; width: 100%; margin: 0 auto; padding-left: 40px; padding-right: 40px; }
  .composer { padding-bottom: 22px; }
  .empty-title { font-size: 32px; }
  .empty-desc { max-width: 400px; }
  .rec-list { display: grid; grid-template-columns: repeat(2, 1fr); gap: 18px; }
  .more-chat-btn { grid-column: 1 / -1; }
}
</style>
