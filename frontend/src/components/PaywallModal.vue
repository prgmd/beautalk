<script setup>
import { ref } from 'vue'

const emit = defineEmits(['close'])

// 결제 단계: 'plans'(요금제 선택) | 'pending'(결제 준비 중 목업)
const step = ref('plans')

const PLANS = [
  {
    id: 'free',
    name: '무료',
    price: '0원',
    period: '',
    features: ['하루 100회 대화', '맞춤 제품 추천', '찜하기'],
    current: true,
  },
  {
    id: 'premium',
    name: '프리미엄',
    price: '4,900원',
    period: '/월',
    features: ['무제한 대화', '맞춤 제품 추천', '찜하기', '대화 기록 무제한 보관'],
    current: false,
    highlight: true,
  },
]

function selectPlan(plan) {
  if (plan.current) return
  step.value = 'pending'
}
</script>

<template>
  <Transition name="modal" appear>
    <div class="overlay" @click="emit('close')">
      <div class="sheet" @click.stop>
        <div class="grab" />
        <button class="close-btn" @click="emit('close')">×</button>

        <!-- 요금제 선택 -->
        <template v-if="step === 'plans'">
          <div class="head">
            <div class="head-icon">✨</div>
            <h2 class="title serif">오늘의 무료 대화를 모두 사용했어요</h2>
            <p class="subtitle">프리미엄으로 업그레이드하면 무제한으로 대화할 수 있어요.</p>
          </div>

          <div class="plans">
            <div
              v-for="plan in PLANS"
              :key="plan.id"
              class="plan-card"
              :class="{ highlight: plan.highlight, current: plan.current }"
            >
              <div class="plan-head">
                <span class="plan-name">{{ plan.name }}</span>
                <span v-if="plan.highlight" class="badge">추천</span>
              </div>
              <div class="plan-price serif">
                {{ plan.price }}<span class="plan-period">{{ plan.period }}</span>
              </div>
              <ul class="plan-features">
                <li v-for="f in plan.features" :key="f">✓ {{ f }}</li>
              </ul>
              <button
                class="plan-btn"
                :class="{ primary: plan.highlight }"
                :disabled="plan.current"
                @click="selectPlan(plan)"
              >
                {{ plan.current ? '현재 이용 중' : '업그레이드' }}
              </button>
            </div>
          </div>

          <p class="footnote">언제든지 해지할 수 있어요.</p>
        </template>

        <!-- 결제 준비 중 (목업) -->
        <template v-else>
          <div class="pending">
            <div class="head-icon">🚧</div>
            <h2 class="title serif">결제 기능 준비 중</h2>
            <p class="subtitle">
              결제 연동은 현재 준비 중이에요.<br />
              정식 오픈 시 프리미엄 플랜을 이용하실 수 있습니다.
            </p>
            <button class="plan-btn primary" @click="emit('close')">확인</button>
          </div>
        </template>
      </div>
    </div>
  </Transition>
</template>

<style scoped>
.overlay {
  position: fixed;
  inset: 0;
  z-index: 200;
  background: rgba(34, 28, 22, 0.42);
  backdrop-filter: blur(6px);
  -webkit-backdrop-filter: blur(6px);
  display: flex;
  align-items: flex-end;
  justify-content: center;
}

.sheet {
  position: relative;
  width: 100%;
  max-width: 480px;
  margin: 0 auto;
  background: var(--card);
  border-radius: 26px 26px 0 0;
  box-shadow: var(--sh-lg);
  max-height: 90vh;
  overflow-y: auto;
  padding: 8px 24px calc(20px + env(safe-area-inset-bottom));
}

.grab {
  width: 36px;
  height: 4px;
  margin: 4px auto 8px;
  border-radius: 999px;
  background: var(--line-strong);
}

.head-icon {
  display: inline-block;
  animation: bt-pop var(--t) var(--ease-back);
}

.close-btn {
  position: absolute;
  top: 14px;
  right: 16px;
  width: 32px;
  height: 32px;
  border-radius: 50%;
  background: var(--panel);
  font-size: 20px;
  color: var(--ink-soft);
  display: flex;
  align-items: center;
  justify-content: center;
  transition: background var(--t-fast) var(--ease);
}
.close-btn:hover { background: var(--line); }

.head { text-align: center; display: flex; flex-direction: column; gap: 8px; margin-bottom: 24px; padding-top: 12px; }
.head-icon { font-size: 40px; }
.title { font-size: 20px; font-weight: 600; color: var(--ink); }
.subtitle { font-size: 13px; color: var(--ink-soft); line-height: 1.65; }

.plans { display: flex; gap: 12px; }

.plan-card {
  flex: 1;
  border: 1px solid var(--line);
  border-radius: var(--radius);
  padding: 18px 16px;
  display: flex;
  flex-direction: column;
  gap: 12px;
  background: var(--sheet);
  transition: transform var(--t) var(--ease), box-shadow var(--t) var(--ease);
}
.plan-card.highlight {
  border-color: var(--sage);
  background: var(--card);
  box-shadow: var(--sh-md);
}
.plan-card.highlight:hover { transform: translateY(-3px); }
.plan-card.current { background: var(--panel); }

.plan-head { display: flex; align-items: center; gap: 6px; }
.plan-name { font-size: 14px; font-weight: 700; color: var(--ink); }
.badge {
  font-size: 10px;
  font-weight: 700;
  background: var(--sage);
  color: var(--card);
  border-radius: 999px;
  padding: 3px 9px;
  box-shadow: var(--sh-sm);
}

.plan-price { font-size: 22px; font-weight: 600; color: var(--ink); }
.plan-period { font-size: 12px; font-weight: 400; color: var(--ink-faint); }

.plan-features {
  list-style: none;
  display: flex;
  flex-direction: column;
  gap: 6px;
  font-size: 12px;
  color: var(--ink-soft);
  flex: 1;
}

.plan-btn {
  width: 100%;
  padding: 11px;
  border: 1px solid var(--line);
  border-radius: var(--radius-sm);
  background: var(--card);
  color: var(--ink);
  font-size: 13px;
  font-weight: 600;
  cursor: pointer;
  transition: transform var(--t-fast) var(--ease), background var(--t-fast) var(--ease), box-shadow var(--t-fast) var(--ease);
}
.plan-btn:hover:not(:disabled) { background: var(--panel); }
.plan-btn.primary {
  background: var(--ink);
  color: var(--canvas);
  border-color: transparent;
  box-shadow: var(--sh-ink);
}
.plan-btn.primary:hover:not(:disabled) { transform: translateY(-1px); }
.plan-btn:disabled { opacity: 0.5; cursor: default; }

.footnote { text-align: center; font-size: 11px; color: var(--ink-faint); margin-top: 16px; }

.pending {
  text-align: center;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 12px;
  padding: 12px 0;
}
.pending .plan-btn { max-width: 160px; margin-top: 8px; }

/* Transition — slide up from bottom */
.modal-enter-active, .modal-leave-active { transition: opacity var(--t) var(--ease); }
.modal-enter-from, .modal-leave-to { opacity: 0; }
.modal-enter-active .sheet, .modal-leave-active .sheet { transition: transform var(--t) var(--ease); }
.modal-enter-from .sheet, .modal-leave-to .sheet { transform: translateY(100%); }
</style>
