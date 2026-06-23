<script setup>
import { ref, onMounted, onUnmounted } from 'vue'

/*
 * 수채화풍 나뭇잎 배경.
 *  · 참고 일러스트의 9종(몬스테라/팜/콜로카시아/바나나/필로덴드론/사고팜/
 *    아랄리아/디펜바키아/아레카팜)을 SVG로 재현해 섞어 깐다.
 *  · 크기를 vmin 단위로 줘서 화면이 아무리 커져도 바닥이 안 보일 만큼 빽빽하다.
 *  · 깊은 초록 그라데이션 바탕 → 혹시 생기는 틈도 잎그늘처럼 보인다.
 *  · 커서 근처 잎만 밀려나며 길이 트이는 '헤집는' 인터랙션 유지.
 */

// 잎 모양 정의. frond(깃털형)는 줄기+잎갈래 선으로, 그 외는 면+잎맥으로 그린다.
const SHAPES = {
  monstera: {
    fill: 'M50 5 C26 12 13 38 16 62 C18 82 33 95 50 95 C67 95 82 82 84 62 C87 38 74 12 50 5 Z M34 42 C31 49 31 58 34 65 C38 58 38 49 34 42 Z M66 42 C69 49 69 58 66 65 C62 58 62 49 66 42 Z',
    veins: 'M50 18 L50 90 M50 40 L30 56 M50 40 L70 56 M50 60 L34 76 M50 60 L66 76',
  },
  colocasia: {
    fill: 'M50 6 C22 6 8 30 8 52 C8 76 28 94 50 94 C72 94 92 76 92 52 C92 30 78 6 50 6 Z',
    veins: 'M50 28 L50 90 M50 40 L22 60 M50 40 L78 60 M50 56 L18 76 M50 56 L82 76 M50 72 L36 90 M50 72 L64 90',
  },
  banana: {
    fill: 'M50 4 C33 14 25 40 29 66 C32 86 44 96 55 96 C62 96 71 86 73 68 C77 40 68 14 50 4 Z',
    veins: 'M52 12 C44 38 41 66 49 92 M50 32 L36 40 M52 32 L66 38 M50 50 L34 60 M52 50 L66 58 M50 68 L40 78 M52 68 L64 76',
  },
  philodendron: {
    fill: 'M50 6 C30 8 20 26 22 44 C15 50 13 62 22 70 C20 80 30 92 44 92 C50 96 58 96 64 90 C78 92 88 80 84 68 C91 60 89 48 80 44 C82 26 70 8 50 6 Z M40 40 C37 47 37 56 40 62 C44 56 44 47 40 40 Z',
    veins: 'M50 18 L52 86 M50 42 L28 54 M52 42 L74 56',
  },
  aralia: {
    fill: 'M50 6 L57 30 L80 22 L65 43 L88 55 L62 55 L66 84 L50 63 L34 84 L38 55 L12 55 L35 43 L20 22 L43 30 Z',
    veins: 'M50 56 L50 12 M50 56 L70 27 M50 56 L30 27 M50 56 L74 54 M50 56 L26 54 M50 56 L63 80 M50 56 L37 80',
  },
  diffenbachia: {
    fill: 'M50 4 C40 18 30 40 30 60 C30 80 40 94 50 96 C60 94 70 80 70 60 C70 40 60 18 50 4 Z',
    veins: 'M50 8 L50 92 M50 26 L36 34 M50 26 L64 34 M50 46 L33 54 M50 46 L67 54 M50 66 L37 74 M50 66 L63 74',
  },
  palm: {
    frond: true,
    rib: 'M50 96 C50 70 52 40 60 6',
    leaflets: 'M52 84 C42 82 36 86 30 92 M53 76 C43 73 37 76 31 82 M54 66 C44 62 38 64 33 70 M55 56 C46 51 40 52 35 58 M56 46 C48 41 43 41 38 46 M57 36 C50 31 45 30 41 35 M52 84 C62 82 68 86 74 92 M53 76 C63 73 69 76 75 82 M54 66 C64 62 70 64 75 70 M55 56 C64 51 70 52 75 58 M56 46 C64 41 69 41 74 46 M57 36 C63 31 67 30 71 35',
  },
  sago: {
    frond: true,
    rib: 'M50 96 L50 6',
    leaflets: 'M50 88 L34 91 M50 79 L34 81 M50 70 L35 71 M50 61 L36 61 M50 52 L37 51 M50 43 L39 41 M50 34 L40 32 M50 25 L42 23 M50 88 L66 91 M50 79 L66 81 M50 70 L65 71 M50 61 L64 61 M50 52 L63 51 M50 43 L61 41 M50 34 L60 32 M50 25 L58 23',
  },
  areca: {
    frond: true,
    rib: 'M48 96 C50 64 56 34 70 6',
    leaflets: 'M51 86 C40 86 33 90 26 96 M52 77 C41 75 35 78 29 85 M53 68 C43 64 37 66 31 73 M54 58 C45 53 39 54 34 61 M55 48 C47 43 42 43 37 49 M56 38 C49 33 45 32 41 38 M57 28 C51 23 48 22 45 27 M51 86 C62 86 69 90 76 96 M52 77 C63 75 69 78 75 85 M53 68 C63 64 69 66 75 73 M54 58 C63 53 69 54 74 61 M55 48 C63 43 68 43 73 49 M56 38 C62 33 66 32 70 38 M57 28 C62 23 65 22 68 27',
  },
}
const TYPES = Object.keys(SHAPES)

// 워터컬러풍 초록 팔레트(밝음→그늘, 일부 청록기)
const GRADS = [
  ['#A6CE82', '#5E9A4F', '#356B36'],
  ['#8CC06E', '#4C8A47', '#2C5C32'],
  ['#B7D78F', '#6FA85B', '#477E45'],
  ['#7FB070', '#3F7A45', '#214E33'],
  ['#9CC58A', '#5E955A', '#3A6E45'],
  ['#8FC2A0', '#4F9277', '#2E6A52'],
]

// 빽빽한 지터 그리드. 크기는 vmin → 화면이 커져도 빈틈 없이 덮인다.
const COLS = 8
const ROWS = 10
const LEAVES = []
for (let r = 0; r < ROWS; r++) {
  for (let c = 0; c < COLS; c++) {
    LEAVES.push({
      x: ((c + 0.5) / COLS) * 116 - 8 + (Math.random() - 0.5) * 18,
      y: ((r + 0.5) / ROWS) * 116 - 8 + (Math.random() - 0.5) * 18,
      s: 17 + Math.random() * 20, // vmin
      rot: Math.random() * 360,
      type: TYPES[Math.floor(Math.random() * TYPES.length)],
      g: GRADS[Math.floor(Math.random() * GRADS.length)],
      flip: Math.random() < 0.5,
      op: 0.92 + Math.random() * 0.08,
      blur: Math.random() < 0.28 ? (0.5 + Math.random() * 0.9).toFixed(2) : 0,
    })
  }
}

// ── 커서 반발(헤집기) ──
const mx = ref(-99999)
const my = ref(-99999)
function onMove(e) { mx.value = e.clientX; my.value = e.clientY }
function onLeave() { mx.value = -99999; my.value = -99999 }

const R = 230
const PUSH = 120
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
    const f = 1 - dist / R
    const e = f * f
    tx = (dx / dist) * e * PUSH
    ty = (dy / dist) * e * PUSH
    lift = e * 14
  }
  return {
    left: leaf.x + '%',
    top: leaf.y + '%',
    width: leaf.s + 'vmin',
    height: leaf.s + 'vmin',
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
          <linearGradient :id="'lg' + i" x1="0.3" y1="0.04" x2="0.62" y2="1">
            <stop offset="0" :stop-color="leaf.g[0]" />
            <stop offset="0.55" :stop-color="leaf.g[1]" />
            <stop offset="1" :stop-color="leaf.g[2]" />
          </linearGradient>
        </defs>

        <!-- 깃털형 잎(팜/사고/아레카) -->
        <template v-if="SHAPES[leaf.type].frond">
          <path :d="SHAPES[leaf.type].rib" :stroke="`url(#lg${i})`" stroke-width="2.6" stroke-linecap="round" fill="none" />
          <path :d="SHAPES[leaf.type].leaflets" :stroke="`url(#lg${i})`" stroke-width="2.3" stroke-linecap="round" fill="none" />
        </template>

        <!-- 면+잎맥형 잎 -->
        <template v-else>
          <path :d="SHAPES[leaf.type].fill" :fill="`url(#lg${i})`" fill-rule="evenodd" />
          <path :d="SHAPES[leaf.type].veins" stroke="#23461F" stroke-width="0.9" fill="none" opacity="0.32" stroke-linecap="round" />
          <path :d="SHAPES[leaf.type].veins" stroke="#FFFFFF" stroke-width="0.5" fill="none" opacity="0.12" stroke-linecap="round" transform="translate(-0.6 -0.6)" />
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
  filter: drop-shadow(0 10px 16px rgba(0, 16, 7, .4));
}
@media (prefers-reduced-motion: reduce) {
  .leaf-wrap { transition: none; }
}
</style>
