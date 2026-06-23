<script setup>
defineProps({
  text: { type: String, default: '' },
  subtitle: { type: String, default: '' },
  size: { type: Number, default: 150 }, // 오브 지름(px)
})
</script>

<template>
  <div class="dewy">
    <div class="orb" :style="{ width: size + 'px', height: size + 'px' }">
      <div class="blob b1" />
      <div class="blob b2" />
      <div class="blob b3" />
      <div class="blob b4" />
      <div class="shine" />
    </div>
    <div v-if="text || subtitle" class="cap">
      <p v-if="text" class="t serif">{{ text }}</p>
      <p v-if="subtitle" class="s">{{ subtitle }}</p>
    </div>
  </div>
</template>

<style scoped>
.dewy { display: flex; flex-direction: column; align-items: center; gap: 24px; }

.orb { position: relative; }
.orb .blob {
  position: absolute;
  inset: 0;
  border-radius: 46% 54% 52% 48% / 50% 46% 54% 50%;
  filter: blur(6px);
  mix-blend-mode: multiply;
  opacity: .85;
}
.orb .b1 { background: radial-gradient(60% 60% at 35% 30%, #FFC2D6, #FF9EBE 70%, transparent); animation: orb-morph 7s ease-in-out infinite, orb-spin 16s linear infinite; }
.orb .b2 { background: radial-gradient(60% 60% at 65% 40%, #CFE3B8, #9FC487 75%, transparent); animation: orb-morph 9s ease-in-out infinite reverse, orb-spin 20s linear infinite reverse; }
.orb .b3 { background: radial-gradient(55% 55% at 50% 70%, #FFE0C2, #FFC59A 75%, transparent); animation: orb-morph 8s ease-in-out infinite, orb-spin 24s linear infinite; }
.orb .b4 { background: radial-gradient(50% 50% at 60% 55%, #D9CCF7, #C3B0F0 78%, transparent); animation: orb-morph 10s ease-in-out infinite reverse; }
.orb .shine {
  position: absolute;
  width: 30%; height: 22%;
  left: 22%; top: 18%;
  border-radius: 50%;
  background: radial-gradient(closest-side, rgba(255,255,255,.95), transparent);
  filter: blur(2px);
  animation: orb-floaty 6s ease-in-out infinite;
}
.orb::after {
  content: '';
  position: absolute;
  inset: -14%;
  border-radius: 50%;
  z-index: -1;
  background: radial-gradient(closest-side, rgba(255,158,190,.28), rgba(159,196,135,.16) 55%, transparent 72%);
  filter: blur(12px);
  animation: orb-breathe 5s ease-in-out infinite;
}

.cap { text-align: center; }
.cap .t { font-size: 18px; font-weight: 400; letter-spacing: -.2px; color: var(--ink); }
.cap .s { font-size: 12.5px; color: var(--ink-soft); margin-top: 7px; line-height: 1.6; }

/* reduce-motion: 외곽 호흡만 유지 */
@media (prefers-reduced-motion: reduce) {
  .orb .blob, .orb .shine { animation: none !important; }
  .orb::after { animation: orb-breathe 6s ease-in-out infinite !important; }
}
</style>
