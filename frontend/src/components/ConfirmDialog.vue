<script setup>
import { watch, nextTick, ref, onUnmounted } from 'vue'
import { useConfirmStore } from '@/stores/confirm'

const confirm = useConfirmStore()
const confirmBtn = ref(null)

function onKey(e) {
  if (e.key === 'Escape') confirm.settle(false)
}

watch(() => confirm.open, (open) => {
  if (open) {
    document.body.style.overflow = 'hidden'
    window.addEventListener('keydown', onKey)
    nextTick(() => confirmBtn.value?.focus())
  } else {
    document.body.style.overflow = ''
    window.removeEventListener('keydown', onKey)
  }
})
onUnmounted(() => {
  document.body.style.overflow = ''
  window.removeEventListener('keydown', onKey)
})
</script>

<template>
  <Teleport to="body">
    <Transition name="cd">
      <div v-if="confirm.open" class="cd-overlay" @click="confirm.settle(false)">
        <div class="cd-sheet" role="dialog" aria-modal="true" :aria-label="confirm.opts.title" @click.stop>
          <h3 class="cd-title serif">{{ confirm.opts.title }}</h3>
          <p v-if="confirm.opts.message" class="cd-msg">{{ confirm.opts.message }}</p>
          <div class="cd-actions">
            <button class="cd-cancel" @click="confirm.settle(false)">{{ confirm.opts.cancelText }}</button>
            <button
              ref="confirmBtn"
              class="cd-confirm" :class="{ danger: confirm.opts.danger }"
              @click="confirm.settle(true)"
            >{{ confirm.opts.confirmText }}</button>
          </div>
        </div>
      </div>
    </Transition>
  </Teleport>
</template>

<style scoped>
.cd-overlay {
  position: fixed; inset: 0; z-index: 320;
  background: rgba(34, 28, 22, .42);
  backdrop-filter: blur(6px); -webkit-backdrop-filter: blur(6px);
  display: flex; align-items: flex-end; justify-content: center;
}
.cd-sheet {
  width: 100%; max-width: 420px; margin: 0 auto;
  background: var(--card); border-radius: 24px 24px 0 0;
  padding: 26px 24px calc(22px + env(safe-area-inset-bottom));
  box-shadow: var(--sh-lg);
  display: flex; flex-direction: column; gap: 10px;
}
.cd-title { font-size: 19px; font-weight: 500; letter-spacing: -.3px; color: var(--ink); }
.cd-msg { font-size: 13.5px; line-height: 1.6; color: var(--ink-soft); }
.cd-actions { display: flex; gap: 8px; margin-top: 14px; }
.cd-cancel, .cd-confirm {
  flex: 1; padding: 13px; border-radius: 99px; font-size: 14px; font-weight: 600;
  transition: transform var(--t-fast) var(--ease);
}
.cd-cancel { border: 1px solid var(--line); background: var(--sheet); color: var(--ink); box-shadow: var(--sh-sm); }
.cd-confirm { border: none; background: var(--ink); color: var(--canvas); box-shadow: var(--sh-ink); }
.cd-confirm.danger { background: var(--danger); color: #fff; }
.cd-cancel:active, .cd-confirm:active { transform: scale(.98); }

.cd-enter-active, .cd-leave-active { transition: opacity var(--t) var(--ease); }
.cd-enter-from, .cd-leave-to { opacity: 0; }
.cd-enter-active .cd-sheet, .cd-leave-active .cd-sheet { transition: transform var(--t) var(--ease); }
.cd-enter-from .cd-sheet, .cd-leave-to .cd-sheet { transform: translateY(100%); }

@media (min-width: 900px) {
  .cd-overlay { align-items: center; }
  .cd-sheet { border-radius: var(--radius-xl); }
  .cd-enter-from .cd-sheet, .cd-leave-to .cd-sheet { transform: scale(.96); }
}
@media (prefers-reduced-motion: reduce) {
  .cd-enter-active, .cd-leave-active, .cd-enter-active .cd-sheet, .cd-leave-active .cd-sheet { transition: none; }
}
</style>
