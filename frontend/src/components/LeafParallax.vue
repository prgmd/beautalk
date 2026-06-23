<script setup>
import { ref, onMounted, onUnmounted } from 'vue'

// 마우스 위치(-1..1). 화면 중앙 기준 오프셋.
const px = ref(0)
const py = ref(0)

// 잎 배치 — 가장자리에 잔뜩 쌓고, 가운데(카드)는 비교적 비운다.
// depth 클수록 더 크게 밀린다(앞쪽). type: split(몬스테라풍) | banana(넓은 잎)
const LEAVES = [
  { x: -4, y: -6, s: 240, r: 18, d: 1.3, t: 'split', c: '#33583A', f: false },
  { x: 8, y: -10, s: 150, r: -22, d: 0.7, t: 'banana', c: '#4E7D52', f: true },
  { x: 22, y: -8, s: 120, r: 40, d: 0.5, t: 'split', c: '#5C8A4A', f: false },
  { x: 38, y: -12, s: 170, r: -12, d: 0.9, t: 'banana', c: '#3F6B39', f: false },
  { x: 60, y: -10, s: 130, r: 28, d: 0.6, t: 'split', c: '#6E9A52', f: true },
  { x: 78, y: -8, s: 200, r: -30, d: 1.1, t: 'banana', c: '#4E7D52', f: false },
  { x: 92, y: -6, s: 250, r: 14, d: 1.35, t: 'split', c: '#33583A', f: true },
  { x: -6, y: 24, s: 180, r: 64, d: 0.95, t: 'banana', c: '#446E3F', f: false },
  { x: 96, y: 26, s: 175, r: -64, d: 0.9, t: 'banana', c: '#446E3F', f: true },
  { x: -7, y: 58, s: 200, r: 110, d: 1.05, t: 'split', c: '#3F6B39', f: false },
  { x: 97, y: 56, s: 195, r: -104, d: 1.0, t: 'split', c: '#3F6B39', f: true },
  { x: -3, y: 96, s: 230, r: 150, d: 1.25, t: 'banana', c: '#33583A', f: true },
  { x: 14, y: 100, s: 150, r: 176, d: 0.7, t: 'split', c: '#5C8A4A', f: false },
  { x: 30, y: 104, s: 175, r: -160, d: 0.85, t: 'banana', c: '#4E7D52', f: true },
  { x: 50, y: 106, s: 140, r: 170, d: 0.55, t: 'split', c: '#6E9A52', f: false },
  { x: 68, y: 104, s: 180, r: 150, d: 0.9, t: 'banana', c: '#3F6B39', f: false },
  { x: 84, y: 100, s: 150, r: -176, d: 0.7, t: 'split', c: '#5C8A4A', f: true },
  { x: 99, y: 96, s: 235, r: -150, d: 1.3, t: 'banana', c: '#33583A', f: false },
  { x: 46, y: -7, s: 96, r: 8, d: 0.35, t: 'split', c: '#8FB46A', f: true },
  { x: 6, y: 70, s: 96, r: 120, d: 0.4, t: 'banana', c: '#7BA05B', f: false },
  { x: 92, y: 74, s: 96, r: -120, d: 0.4, t: 'banana', c: '#7BA05B', f: true },
]

function onMove(e) {
  px.value = (e.clientX / window.innerWidth - 0.5) * 2
  py.value = (e.clientY / window.innerHeight - 0.5) * 2
}

const K = 30 // 최대 밀림(px)
function styleFor(leaf) {
  const tx = -px.value * leaf.d * K
  const ty = -py.value * leaf.d * K
  return {
    left: leaf.x + '%',
    top: leaf.y + '%',
    width: leaf.s + 'px',
    height: leaf.s + 'px',
    transform: `translate3d(${tx}px, ${ty}px, 0) rotate(${leaf.r}deg) scaleX(${leaf.f ? -1 : 1})`,
  }
}

onMounted(() => window.addEventListener('mousemove', onMove, { passive: true }))
onUnmounted(() => window.removeEventListener('mousemove', onMove))
</script>

<template>
  <div class="leaves" aria-hidden="true">
    <svg
      v-for="(leaf, i) in LEAVES"
      :key="i"
      class="leaf"
      :style="styleFor(leaf)"
      viewBox="0 0 100 100"
    >
      <!-- 몬스테라풍 갈라진 잎 -->
      <template v-if="leaf.t === 'split'">
        <path
          d="M50 3 C26 16 17 50 32 82 C38 96 50 91 50 79 C50 91 62 96 68 82 C83 50 74 16 50 3 Z"
          :fill="leaf.c"
        />
        <path d="M50 14 C50 40 50 62 50 80" :stroke="leaf.c" stroke-width="1.4" fill="none" stroke-linecap="round" filter="brightness(.7)" opacity="0.5" />
        <path d="M50 36 C42 40 38 46 35 56 M50 52 C44 55 41 60 39 68" :stroke="leaf.c" stroke-width="1" fill="none" opacity="0.4" />
        <path d="M50 36 C58 40 62 46 65 56 M50 52 C56 55 59 60 61 68" :stroke="leaf.c" stroke-width="1" fill="none" opacity="0.4" />
      </template>
      <!-- 넓은 바나나 잎 -->
      <template v-else>
        <path
          d="M50 3 C29 8 19 32 21 60 C23 88 40 97 50 97 C60 97 77 88 79 60 C81 32 71 8 50 3 Z"
          :fill="leaf.c"
        />
        <path d="M50 12 C50 40 50 70 50 94" :stroke="leaf.c" stroke-width="1.4" fill="none" opacity="0.45" />
        <path d="M50 30 C40 34 33 42 28 54 M50 50 C41 54 35 62 31 74 M50 70 C43 74 38 80 35 88" :stroke="leaf.c" stroke-width="0.9" fill="none" opacity="0.35" />
        <path d="M50 30 C60 34 67 42 72 54 M50 50 C59 54 65 62 69 74 M50 70 C57 74 62 80 65 88" :stroke="leaf.c" stroke-width="0.9" fill="none" opacity="0.35" />
      </template>
    </svg>
  </div>
</template>

<style scoped>
.leaves {
  position: absolute;
  inset: 0;
  overflow: hidden;
  pointer-events: none;
  z-index: 0;
}
.leaf {
  position: absolute;
  translate: -50% -50%;
  opacity: .9;
  filter: drop-shadow(0 6px 12px rgba(34, 50, 30, .14)) saturate(1.05);
  transition: transform .45s cubic-bezier(0.22, 1, 0.36, 1);
  will-change: transform;
}
@media (prefers-reduced-motion: reduce) {
  .leaf { transition: none; }
}
</style>
