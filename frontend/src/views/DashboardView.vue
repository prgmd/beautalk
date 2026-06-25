<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import { useProfileStore } from '@/stores/profile'
import { api } from '@/services/api'
import GlobalSidebar from '@/components/GlobalSidebar.vue'
import Icon from '@/components/Icon.vue'

const router = useRouter()
const auth = useAuthStore()
const profile = useProfileStore()

const userName = computed(() => {
  const u = auth.user
  if (!u) return ''
  if (u.nickname) return u.nickname
  if (u.email) return u.email.split('@')[0]
  return ''
})

// ── 날씨 ──
const weather = ref({ condition: 'default', temp: null, desc: '' })
const WX_ICON = { clear: '☀️', rain: '🌧️', snow: '❄️', clouds: '☁️', default: '🌿' }
const WX_FACE = { clear: '☀️', rain: '🌧️', snow: '⛄', clouds: '☁️', default: '🌿' }
const WX_MSG = {
  clear:  '햇살이 반짝여요!',
  rain:   '비가 토닥토닥',
  snow:   '눈이 소복소복',
  clouds: '포근하게 흐려요',
  default: '오늘도 좋은 하루!',
}
const wxIcon = computed(() => WX_ICON[weather.value.condition] || WX_ICON.default)
const wxFace = computed(() => WX_FACE[weather.value.condition] || WX_FACE.default)
const wxMsg = computed(() => WX_MSG[weather.value.condition] || WX_MSG.default)

// 날씨 기반 제안 문구 (상담 화면과 동일 톤)
const WX_SUGGEST = {
  clear:  '맑고 자외선이 강한 날이에요. 선크림을 꼭 챙겨보는 건 어떨까요?',
  rain:   '비가 내리고 있어요. 워터프루프 제품을 챙겨보는 건 어떨까요?',
  snow:   '춥고 건조한 날씨예요. 보습 크림으로 피부를 지켜보는 건 어떨까요?',
  clouds: '흐린 날인만큼 자외선 차단을 신경 써보는 건 어떨까요?',
}
const suggestLine = computed(() => {
  if (weather.value.temp == null) return ''
  return WX_SUGGEST[weather.value.condition] || ''
})

// ── 프로필 요약 ──
const hasProfile = computed(() => !!profile.skinType)

onMounted(async () => {
  try {
    const { data } = await api.get('/weather/', { auth: false })
    if (data?.condition) weather.value = data
  } catch { /* 키 없으면 무시 */ }
  if (!profile.loaded) profile.fetchProfile().catch(() => {})
})

function go(path) { router.push(path) }
</script>

<template>
  <div class="screen">
    <div class="main">
      <div class="page">
        <!-- 인사 -->
        <header class="greeting">
          <p class="hello">
            <span class="serif name">{{ userName || '회원' }}</span>님, 안녕하세요 👋
          </p>
          <p v-if="suggestLine" class="suggest">{{ suggestLine }}</p>
        </header>

        <!-- 귀여운 1:1 날씨 타일 + 프로필 요약 -->
        <div class="top-grid">
          <div class="wx-tile" :class="'wx-' + weather.condition">
            <!-- 장식: 반짝이 -->
            <span class="spark s1">✦</span>
            <span class="spark s2">✦</span>
            <span class="spark s3">·</span>
            <!-- 비/눈 입자 (조건별 표시) -->
            <div class="particles" aria-hidden="true">
              <span v-for="n in 6" :key="n" class="particle" :style="{ '--i': n }" />
            </div>

            <div class="wx-face">{{ wxFace }}</div>
            <p class="wx-temp">{{ weather.temp != null ? weather.temp + '°' : '—' }}</p>
            <p class="wx-msg">{{ wxMsg }}</p>
            <p class="wx-city">서울 · {{ weather.desc || '오늘의 날씨' }}</p>
          </div>

          <!-- 내 피부 프로필 요약 -->
        <section class="profile-card" @click="go('/mypage/profile')">
          <span class="pc-leaf" aria-hidden="true">❋</span>
          <div class="pc-head">
            <span class="pc-label">내 피부 프로필</span>
            <span class="pc-go">관리 ›</span>
          </div>
          <div class="pc-body">
            <template v-if="hasProfile">
              <p class="pc-skin serif">{{ profile.skinType }} <span class="pc-skin-suffix">피부</span></p>
              <div v-if="profile.concerns.length" class="pc-chips">
                <span v-for="c in profile.concerns" :key="c" class="pc-chip">{{ c }}</span>
              </div>
              <p v-else class="pc-empty-sub">고민을 추가하면 더 정확한 추천을 받을 수 있어요.</p>
            </template>
            <template v-else>
              <p class="pc-skin serif">아직 피부 타입이<br>없어요</p>
              <p class="pc-empty-sub">피부 타입 진단을 받거나 프로필을 설정해 보세요.</p>
            </template>
          </div>
        </section>
        </div>

        <!-- 상담 2종 -->
        <p class="sec-title">무엇을 도와드릴까요?</p>
        <div class="consult-grid">
          <button class="consult-card primary" @click="go('/chat')">
            <span class="cc-emoji">💌</span>
            <span class="cc-title">화장품 추천</span>
            <span class="cc-desc">대화로 내 피부에 맞는<br>제품을 찾아드려요</span>
            <span class="cc-cta">상담 시작 →</span>
          </button>
          <button class="consult-card" @click="go('/consult/skin')">
            <span class="cc-emoji">🧪</span>
            <span class="cc-title">피부 타입 진단</span>
            <span class="cc-desc">몇 가지 질문으로<br>내 피부 타입을 알아봐요</span>
            <span class="cc-cta">진단 시작 →</span>
          </button>
        </div>

        <!-- 바로가기 -->
        <p class="sec-title">바로가기</p>
        <div class="quick-row">
          <button class="quick" @click="go('/community')">
            <span class="q-emoji">💬</span><span class="q-label">커뮤니티</span>
          </button>
          <button class="quick" @click="go('/catalog')">
            <span class="q-emoji">🛍️</span><span class="q-label">둘러보기</span>
          </button>
          <button class="quick" @click="go('/mypage/recommended')">
            <span class="q-emoji">✨</span><span class="q-label">추천 내역</span>
          </button>
          <button class="quick" @click="go('/mypage/liked')">
            <span class="q-emoji">🤍</span><span class="q-label">찜한 제품</span>
          </button>
        </div>
      </div>
    </div>

    <GlobalSidebar />
  </div>
</template>

<style scoped>
.screen { height: 100%; display: flex; flex-direction: column; overflow: hidden; }
.main { flex: 1; min-height: 0; display: flex; flex-direction: column; overflow-y: auto; }
.page {
  width: 100%; max-width: 560px; margin: 0 auto;
  padding: calc(20px + env(safe-area-inset-top)) 20px 32px;
  display: flex; flex-direction: column; gap: 20px;
}

/* 인사 */
.greeting { animation: bt-rise .4s var(--ease) both; }
.hello { font-size: 22px; font-weight: 500; color: var(--ink); letter-spacing: -.3px; }
.hello .name { font-style: italic; }
.suggest { font-size: 13.5px; color: var(--ink-soft); margin-top: 8px; line-height: 1.55; }

/* ── 상단 그리드: 날씨 타일 + 프로필 ── */
.top-grid { display: grid; grid-template-columns: minmax(0,0.85fr) 1.15fr; gap: 12px; align-items: stretch; }

/* 귀여운 1:1 날씨 타일 */
.wx-tile {
  position: relative; overflow: hidden;
  aspect-ratio: 1 / 1;
  border-radius: 24px;
  border: 1px solid var(--line-soft);
  display: flex; flex-direction: column; align-items: center; justify-content: center;
  gap: 2px; text-align: center; padding: 12px;
  box-shadow: var(--sh-soft);
  animation: bt-rise .45s var(--ease) .04s both;
  background: linear-gradient(160deg, #FCEFD6, #FBE3C6);
}
.wx-tile.wx-clear  { background: linear-gradient(160deg, #FFE9B0, #FFD08A); }
.wx-tile.wx-clouds { background: linear-gradient(160deg, #E7EAF0, #D6DCE6); }
.wx-tile.wx-rain   { background: linear-gradient(160deg, #D4E4F2, #B9CFE8); }
.wx-tile.wx-snow   { background: linear-gradient(160deg, #EAF4FB, #D4E9F7); }

.wx-face {
  font-size: 46px; line-height: 1;
  filter: drop-shadow(0 3px 6px rgba(0,0,0,.12));
  animation: wx-bob 3s ease-in-out infinite;
}
@keyframes wx-bob {
  0%, 100% { transform: translateY(0) rotate(-3deg); }
  50%       { transform: translateY(-6px) rotate(3deg); }
}
.wx-temp { font-size: 30px; font-weight: 800; color: #5a4a36; letter-spacing: -1px; margin-top: 2px; }
.wx-msg { font-size: 13px; font-weight: 700; color: #6b5942; }
.wx-city { font-size: 10.5px; font-weight: 600; color: rgba(90,74,54,.6); margin-top: 2px; }

/* 반짝이 장식 */
.spark { position: absolute; color: #fff; opacity: .85; pointer-events: none; text-shadow: 0 1px 2px rgba(0,0,0,.08); }
.spark.s1 { top: 14px; right: 16px; font-size: 13px; animation: twinkle 2.4s ease-in-out infinite; }
.spark.s2 { bottom: 18px; left: 16px; font-size: 10px; animation: twinkle 2.4s ease-in-out infinite .8s; }
.spark.s3 { top: 22px; left: 22px; font-size: 16px; animation: twinkle 2.4s ease-in-out infinite 1.4s; }
@keyframes twinkle {
  0%, 100% { opacity: .25; transform: scale(.7); }
  50%       { opacity: 1; transform: scale(1.1); }
}

/* 비/눈 입자 — rain·snow에서만 보이게 */
.particles { position: absolute; inset: 0; pointer-events: none; }
.particle {
  position: absolute; top: -10%; left: calc(var(--i) * 16% - 4%);
  width: 4px; height: 4px; border-radius: 50%;
  opacity: 0;
}
.wx-rain .particle {
  width: 2px; height: 12px; border-radius: 2px; background: rgba(90,130,190,.5);
  animation: fall 0.9s linear infinite; animation-delay: calc(var(--i) * .13s);
}
.wx-snow .particle {
  background: rgba(255,255,255,.95);
  animation: fall 2.6s linear infinite; animation-delay: calc(var(--i) * .35s);
}
@keyframes fall {
  0%   { opacity: 0; transform: translateY(0); }
  10%  { opacity: 1; }
  90%  { opacity: 1; }
  100% { opacity: 0; transform: translateY(180px); }
}

@media (prefers-reduced-motion: reduce) {
  .wx-face, .spark, .particle { animation: none; }
}

/* 프로필 요약 카드 — 날씨 타일과 같은 높이를 위·아래로 꽉 채운다 */
.profile-card {
  position: relative; overflow: hidden;
  text-align: left; cursor: pointer;
  background: var(--card); border: 1px solid var(--line-soft); border-radius: 24px;
  padding: 20px 22px; box-shadow: var(--sh-soft);
  display: flex; flex-direction: column; justify-content: space-between;
  transition: transform var(--t) var(--ease), box-shadow var(--t) var(--ease);
  animation: bt-rise .45s var(--ease) .04s both;
}
.profile-card:hover { transform: translateY(-2px); box-shadow: var(--sh-hover); }
.pc-leaf {
  position: absolute; top: -14px; right: -8px;
  font-size: 84px; line-height: 1; color: var(--sage-soft);
  pointer-events: none; user-select: none; z-index: 0;
}
.pc-head { position: relative; z-index: 1; display: flex; align-items: center; justify-content: space-between; }
.pc-label { font-size: 10px; letter-spacing: 2px; text-transform: uppercase; color: var(--ink-faint); font-weight: 600; }
.pc-go { font-size: 12px; color: var(--sage-ink); font-weight: 700; }
.pc-body { position: relative; z-index: 1; display: flex; flex-direction: column; gap: 12px; }
.pc-skin { font-size: 27px; font-weight: 500; color: var(--ink); line-height: 1.15; }
.pc-skin-suffix { font-size: 18px; color: var(--ink-soft); }
.pc-chips { display: flex; flex-wrap: wrap; gap: 6px; }
.pc-chip { font-size: 12px; font-weight: 600; padding: 5px 11px; border-radius: 99px; background: var(--sage-soft); color: var(--sage-ink); }
.pc-empty-sub { font-size: 12.5px; color: var(--ink-faint); line-height: 1.5; }

/* 섹션 타이틀 */
.sec-title { font-size: 14px; font-weight: 700; color: var(--ink); margin: 4px 2px -4px; }

/* 상담 2종 */
.consult-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 12px; }
.consult-card {
  text-align: left; display: flex; flex-direction: column; gap: 6px;
  padding: 18px; border-radius: var(--radius-lg); min-height: 168px;
  background: var(--card); border: 1px solid var(--line-soft); box-shadow: var(--sh-soft);
  transition: transform var(--t) var(--ease), box-shadow var(--t) var(--ease), border-color var(--t-fast);
  animation: bt-rise .5s var(--ease) .08s both;
}
.consult-card:hover { transform: translateY(-3px); box-shadow: var(--sh-hover); border-color: var(--sage); }
.consult-card.primary { background: linear-gradient(165deg, var(--sage-soft), var(--card)); border-color: var(--line); }
.cc-emoji { font-size: 30px; line-height: 1; }
.cc-title { font-size: 16px; font-weight: 700; color: var(--ink); margin-top: 4px; }
.cc-desc { font-size: 12px; color: var(--ink-soft); line-height: 1.5; flex: 1; }
.cc-cta { font-size: 13px; font-weight: 700; color: var(--sage-ink); }

/* 바로가기 */
.quick-row { display: grid; grid-template-columns: repeat(4, 1fr); gap: 10px; }
.quick {
  display: flex; flex-direction: column; align-items: center; gap: 7px;
  padding: 14px 6px; border-radius: var(--radius);
  background: var(--sheet); border: 1px solid var(--line-soft);
  transition: transform var(--t-fast) var(--ease), border-color var(--t-fast);
  animation: bt-rise .5s var(--ease) .12s both;
}
.quick:hover { border-color: var(--sage); }
.quick:active { transform: scale(.96); }
.q-emoji { font-size: 22px; line-height: 1; }
.q-label { font-size: 11.5px; font-weight: 600; color: var(--ink-soft); }

@media (min-width: 900px) {
  .screen { flex-direction: row; }
  .page { max-width: 760px; padding: 44px 40px 52px; gap: 26px; }
  .hello { font-size: 30px; }
  .suggest { font-size: 15px; margin-top: 10px; }
  .sec-title { font-size: 17px; }

  /* 날씨 타일 */
  .wx-face { font-size: 56px; }
  .wx-temp { font-size: 38px; }
  .wx-msg { font-size: 15px; }
  .wx-city { font-size: 12px; }

  /* 프로필 요약 */
  .pc-label { font-size: 11px; }
  .pc-skin { font-size: 32px; }
  .pc-skin-suffix { font-size: 21px; }
  .pc-chip { font-size: 12.5px; }
  .pc-empty-sub { font-size: 13.5px; }

  /* 상담 카드 */
  .consult-card { min-height: 196px; }
  .cc-emoji { font-size: 36px; }
  .cc-title { font-size: 18px; }
  .cc-desc { font-size: 13px; }
  .cc-cta { font-size: 14px; }

  /* 바로가기 */
  .q-emoji { font-size: 26px; }
  .q-label { font-size: 13px; }
}
</style>
