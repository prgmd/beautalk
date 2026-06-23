<script setup>
import { ref, onMounted, onUnmounted } from 'vue'

// 빛(위)→그늘(아래) 잎 그라데이션 세트
const GRADS = [
  ['#8CC06E', '#3C6B3C'],
  ['#79B05E', '#2F5C39'],
  ['#9ECB78', '#4E8550'],
  ['#69A557', '#234E35'],
  ['#A9CE80', '#56934F'],
  ['#72AB5B', '#356143'],
  ['#8FC06E', '#43763F'],
]

// 화면을 빈틈없이 덮도록 지터 그리드 배치(가장자리는 살짝 화면 밖으로 넘침)
const COLS = 7
const ROWS = 9
const LEAVES = []
for (let r = 0; r < ROWS; r++) {
  for (let c = 0; c < COLS; c++) {
    LEAVES.push({
      x: ((c + 0.5) / COLS) * 110 - 5 + (Math.random() - 0.5) * 18,
      y: ((r + 0.5) / ROWS) * 110 - 5 + (Math.random() - 0.5) * 18,
      s: 150 + Math.random() * 210,
      rot: Math.random() * 360,
      t: Math.random() < 0.5 ? 'split' : 'banana',
      g: GRADS[Math.floor(Math.random() * GRADS.length)],
      flip: Math.random() < 0.5,
      op: 0.9 + Math.random() * 0.1,
      blur: Math.random() < 0.3 ? (0.6 + Math.random() * 0.8).toFixed(2) : 0, // 일부는 살짝 흐려 원경감
    })
  }
}

// 커서 위치(없으면 화면 밖)
const mx = ref(-99999)
const my = ref(-99999)

function onMove(e) { mx.value = e.clientX; my.value = e.clientY }
function onLeave() { mx.value = -99999; my.value = -99999 }

const R = 230 // 영향 반경(px)
const PUSH = 115 // 최대 비켜남(px)

function wrapStyle(leaf) {
  const vw = window.innerWidth || 1
  const vh = window.innerHeight || 1
  const lx = (leaf.x / 100) * vw
  const ly = (leaf.y / 100) * vh
  const dx = lx - mx.value
  const dy = ly - my.value
  const dist = Math.hypot(dx, dy) || 1
  let tx = 0
  let ty = 0
  let lift = 0
  if (dist < R) {
    const f = 1 - dist / R // 0..1 (가까울수록 크게)
    const e = f * f // 부드러운 가속(고급스럽게)
    tx = (dx / dist) * e * PUSH
    ty = (dy / dist) * e * PUSH
    lift = e * 14
  }
  return {
    left: leaf.x + '%',
    top: leaf.y + '%',
    width: leaf.s + 'px',
    height: leaf.s + 'px',
    transform: `translate3d(${tx}px, ${ty - lift}px, 0) rotate(${leaf.rot}deg) scaleX(${leaf.flip ? -1 : 1})`,
    opacity: leaf.op,
    filter: leaf.blur ? `blur(${leaf.blur}px)` : 'none',
  }
}

onMounted(() => {
  window.addEventListener('mousemove', onMove, { passive: true })
  window.addEventListener('mouseleave', onLeave)
})
onUnmounted(() => {
  window.removeEventListener('mousemove', onMove)
  window.removeEventListener('mouseleave', onLeave)
})
</script>

<template>
  <div class="leaves" aria-hidden="true">
    <div v-for="(leaf, i) in LEAVES" :key="i" class="leaf-wrap" :style="wrapStyle(leaf)">
      <svg class="leaf" viewBox="0 0 100 100">
        <defs>
          <linearGradient :id="'lg' + i" x1="0.32" y1="0.05" x2="0.62" y2="1">
            <stop offset="0" :stop-color="leaf.g[0]" />
            <stop offset="1" :stop-color="leaf.g[1]" />
          </linearGradient>
        </defs>
        <template v-if="leaf.t === 'split'">
          <path d="M50 3 C26 16 17 50 32 82 C38 96 50 91 50 79 C50 91 62 96 68 82 C83 50 74 16 50 3 Z" :fill="`url(#lg${i})`" />
          <path d="M50 13 C50 40 50 62 50 80" stroke="#13321F" stroke-width="1.3" fill="none" opacity="0.4" stroke-linecap="round" />
          <path d="M50 36 C42 41 38 47 35 58 M50 53 C44 56 41 61 39 70 M50 26 C44 29 41 33 39 40" stroke="#13321F" stroke-width="0.8" fill="none" opacity="0.3" />
          <path d="M50 36 C58 41 62 47 65 58 M50 53 C56 56 59 61 61 70 M50 26 C56 29 59 33 61 40" stroke="#13321F" stroke-width="0.8" fill="none" opacity="0.3" />
          <path d="M44 14 C34 24 29 42 33 60" stroke="#FFFFFF" stroke-width="1.4" fill="none" opacity="0.16" stroke-linecap="round" />
        </template>
        <template v-else>
          <path d="M50 3 C29 8 19 32 21 60 C23 88 40 97 50 97 C60 97 77 88 79 60 C81 32 71 8 50 3 Z" :fill="`url(#lg${i})`" />
          <path d="M50 11 C50 40 50 70 50 94" stroke="#13321F" stroke-width="1.3" fill="none" opacity="0.38" stroke-linecap="round" />
          <path d="M50 28 C40 33 33 41 28 53 M50 48 C41 52 35 60 31 72 M50 68 C43 72 38 78 35 86" stroke="#13321F" stroke-width="0.75" fill="none" opacity="0.28" />
          <path d="M50 28 C60 33 67 41 72 53 M50 48 C59 52 65 60 69 72 M50 68 C57 72 62 78 65 86" stroke="#13321F" stroke-width="0.75" fill="none" opacity="0.28" />
          <path d="M44 12 C33 30 30 56 36 84" stroke="#FFFFFF" stroke-width="1.6" fill="none" opacity="0.15" stroke-linecap="round" />
        </template>
      </svg>
    </div>
  </div>
</template>

<style scoped>
.leaves {
  position: absolute;
  inset: 0;
  overflow: hidden;
  pointer-events: none;
  z-index: 0;
  background: radial-gradient(ellipse 95% 85% at 50% 42%, #1C422F 0%, #112E1E 55%, #08190F 100%);
}
.leaf-wrap {
  position: absolute;
  translate: -50% -50%;
  transition: transform .55s cubic-bezier(0.16, 1, 0.3, 1);
  will-change: transform;
}
.leaf {
  display: block;
  width: 100%;
  height: 100%;
  filter: drop-shadow(0 12px 18px rgba(0, 16, 7, .42));
}
@media (prefers-reduced-motion: reduce) {
  .leaf-wrap { transition: none; }
}
</style>
