<script setup>
import { ref, onMounted, onUnmounted } from 'vue'

// 마우스 위치(-1..1)
const px = ref(0)
const py = ref(0)

const GREENS = ['#2E5A38', '#3F7245', '#56934F', '#6FA85A', '#3A6B4A', '#88BA63', '#245036', '#4E8550', '#5E9A57']

// 화면을 빈틈없이 덮도록 지터 그리드로 잎을 배치한다(가장자리는 화면 밖으로 살짝 넘침).
const COLS = 7
const ROWS = 9
const LEAVES = []
for (let r = 0; r < ROWS; r++) {
  for (let c = 0; c < COLS; c++) {
    const jx = (Math.random() - 0.5) * 18
    const jy = (Math.random() - 0.5) * 18
    LEAVES.push({
      x: ((c + 0.5) / COLS) * 108 - 4 + jx,
      y: ((r + 0.5) / ROWS) * 108 - 4 + jy,
      s: 140 + Math.random() * 190, // 140~330px
      rot: Math.random() * 360,
      d: 0.35 + Math.random() * 1.05, // 패럴랙스 depth
      t: Math.random() < 0.5 ? 'split' : 'banana',
      c: GREENS[Math.floor(Math.random() * GREENS.length)],
      flip: Math.random() < 0.5,
      dur: (3.4 + Math.random() * 3.2).toFixed(2), // 흔들림 주기
      delay: (Math.random() * 4).toFixed(2),
      op: 0.82 + Math.random() * 0.18,
    })
  }
}

function onMove(e) {
  px.value = (e.clientX / window.innerWidth - 0.5) * 2
  py.value = (e.clientY / window.innerHeight - 0.5) * 2
}

const K = 34 // 최대 밀림(px)
function wrapStyle(leaf) {
  const tx = -px.value * leaf.d * K
  const ty = -py.value * leaf.d * K
  return {
    left: leaf.x + '%',
    top: leaf.y + '%',
    width: leaf.s + 'px',
    height: leaf.s + 'px',
    transform: `translate3d(${tx}px, ${ty}px, 0) rotate(${leaf.rot}deg) scaleX(${leaf.flip ? -1 : 1})`,
  }
}

onMounted(() => window.addEventListener('mousemove', onMove, { passive: true }))
onUnmounted(() => window.removeEventListener('mousemove', onMove))
</script>

<template>
  <div class="leaves" aria-hidden="true">
    <div
      v-for="(leaf, i) in LEAVES"
      :key="i"
      class="leaf-wrap"
      :style="wrapStyle(leaf)"
    >
      <svg
        class="leaf"
        :style="{ animationDuration: leaf.dur + 's', animationDelay: leaf.delay + 's', opacity: leaf.op }"
        viewBox="0 0 100 100"
      >
        <template v-if="leaf.t === 'split'">
          <path d="M50 3 C26 16 17 50 32 82 C38 96 50 91 50 79 C50 91 62 96 68 82 C83 50 74 16 50 3 Z" :fill="leaf.c" />
          <path d="M50 14 C50 40 50 62 50 80" stroke="#1c3a26" stroke-width="1.2" fill="none" opacity="0.35" />
          <path d="M50 38 C42 42 38 48 35 58 M50 54 C44 57 41 62 39 70" stroke="#1c3a26" stroke-width="0.9" fill="none" opacity="0.28" />
          <path d="M50 38 C58 42 62 48 65 58 M50 54 C56 57 59 62 61 70" stroke="#1c3a26" stroke-width="0.9" fill="none" opacity="0.28" />
        </template>
        <template v-else>
          <path d="M50 3 C29 8 19 32 21 60 C23 88 40 97 50 97 C60 97 77 88 79 60 C81 32 71 8 50 3 Z" :fill="leaf.c" />
          <path d="M50 12 C50 40 50 70 50 94" stroke="#1c3a26" stroke-width="1.2" fill="none" opacity="0.33" />
          <path d="M50 30 C40 34 33 42 28 54 M50 50 C41 54 35 62 31 74 M50 70 C43 74 38 80 35 88" stroke="#1c3a26" stroke-width="0.8" fill="none" opacity="0.26" />
          <path d="M50 30 C60 34 67 42 72 54 M50 50 C59 54 65 62 69 74 M50 70 C57 74 62 80 65 88" stroke="#1c3a26" stroke-width="0.8" fill="none" opacity="0.26" />
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
  background: radial-gradient(ellipse 90% 80% at 50% 42%, #1B402E 0%, #11301F 55%, #0A2014 100%);
}
.leaf-wrap {
  position: absolute;
  translate: -50% -50%;
  transition: transform .5s cubic-bezier(0.22, 1, 0.36, 1);
  will-change: transform;
}
.leaf {
  display: block;
  width: 100%;
  height: 100%;
  transform-origin: 50% 88%;
  filter: drop-shadow(0 8px 14px rgba(0, 20, 10, .35));
  animation-name: leaf-sway;
  animation-timing-function: ease-in-out;
  animation-iteration-count: infinite;
  animation-direction: alternate;
  will-change: transform;
}
@keyframes leaf-sway {
  from { transform: rotate(-3.2deg) translateY(2px); }
  to { transform: rotate(3.2deg) translateY(-4px); }
}
@media (prefers-reduced-motion: reduce) {
  .leaf-wrap { transition: none; }
  .leaf { animation: none; }
}
</style>
