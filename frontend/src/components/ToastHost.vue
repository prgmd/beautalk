<script setup>
import { useToastStore } from '@/stores/toast'
const toast = useToastStore()
</script>

<template>
  <Teleport to="body">
    <div class="toast-host" role="status" aria-live="polite">
      <TransitionGroup name="toast">
        <button
          v-for="t in toast.items" :key="t.id"
          class="toast" :class="t.type"
          @click="toast.dismiss(t.id)"
        >
          <span class="t-ic">{{ t.type === 'success' ? '✓' : t.type === 'error' ? '!' : 'ⓘ' }}</span>
          <span class="t-msg">{{ t.message }}</span>
        </button>
      </TransitionGroup>
    </div>
  </Teleport>
</template>

<style scoped>
.toast-host {
  position: fixed;
  left: 0; right: 0;
  bottom: calc(78px + env(safe-area-inset-bottom));
  z-index: 400;
  display: flex; flex-direction: column; align-items: center; gap: 8px;
  pointer-events: none;
  padding: 0 16px;
}
.toast {
  pointer-events: auto;
  display: inline-flex; align-items: center; gap: 9px;
  max-width: 92vw;
  padding: 12px 16px; border-radius: 99px;
  background: var(--ink); color: var(--canvas);
  font-size: 13.5px; font-weight: 600; line-height: 1.4;
  box-shadow: var(--sh-lg);
}
.toast.success { background: var(--sage-ink); }
.toast.error { background: var(--danger); }
.t-ic {
  flex-shrink: 0; width: 18px; height: 18px; border-radius: 50%;
  display: flex; align-items: center; justify-content: center;
  font-size: 12px; background: rgba(255, 255, 255, .22);
}
.t-msg { text-align: left; }

.toast-enter-active, .toast-leave-active { transition: opacity .25s var(--ease), transform .25s var(--ease); }
.toast-enter-from, .toast-leave-to { opacity: 0; transform: translateY(10px); }

@media (min-width: 900px) {
  .toast-host { bottom: 28px; }
}
@media (prefers-reduced-motion: reduce) {
  .toast-enter-active, .toast-leave-active { transition: none; }
}
</style>
