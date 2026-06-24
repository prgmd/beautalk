<script setup>
// 커스텀 라인 아이콘 세트(이모지 대체). 24 그리드, currentColor, 둥근 캡.
defineProps({
  name: { type: String, required: true },
  size: { type: [Number, String], default: 20 },
  stroke: { type: Number, default: 1.7 },
})

const ICONS = {
  search: '<circle cx="11" cy="11" r="7"/><path d="M16.5 16.5 21 21"/>',
  x: '<path d="M6 6 18 18M18 6 6 18"/>',
  heart: '<path d="M12 20.4C12 20.4 3.5 15.4 3.5 9.2 3.5 6.3 5.7 4.5 8 4.5c1.8 0 3.2 1.1 4 2.4.8-1.3 2.2-2.4 4-2.4 2.3 0 4.5 1.8 4.5 4.7 0 6.2-8.5 11.2-8.5 11.2Z"/>',
  'heart-fill': '<path d="M12 20.4C12 20.4 3.5 15.4 3.5 9.2 3.5 6.3 5.7 4.5 8 4.5c1.8 0 3.2 1.1 4 2.4.8-1.3 2.2-2.4 4-2.4 2.3 0 4.5 1.8 4.5 4.7 0 6.2-8.5 11.2-8.5 11.2Z" fill="currentColor" stroke="none"/>',
  leaf: '<path d="M4.5 19.5C4.5 11 9.5 5.5 20 4.5 19 14 13.5 19.5 5.5 19.5"/><path d="M8.5 16.5C11 12.5 14 9.5 18 7.5"/>',
  external: '<path d="M10 6H6.5A2.5 2.5 0 0 0 4 8.5v9A2.5 2.5 0 0 0 6.5 20h9a2.5 2.5 0 0 0 2.5-2.5V14"/><path d="M14.5 4H20v5.5"/><path d="M20 4 11.5 12.5"/>',
  sparkle: '<path d="M12 3.5 13.7 8.3 18.5 10 13.7 11.7 12 16.5 10.3 11.7 5.5 10 10.3 8.3Z" fill="currentColor" stroke="none"/><path d="M18.6 14.5 19.5 16.6 21.5 17.5 19.5 18.4 18.6 20.5 17.7 18.4 15.6 17.5 17.7 16.6Z" fill="currentColor" stroke="none"/>',
  tag: '<path d="M11.5 3H18a3 3 0 0 1 3 3v6.5a2 2 0 0 1-.6 1.4l-7 7a2 2 0 0 1-2.8 0l-5.5-5.5a2 2 0 0 1 0-2.8l7-7A2 2 0 0 1 11.5 3Z"/><circle cx="16" cy="8" r="1.3" fill="currentColor" stroke="none"/>',
  plus: '<path d="M12 5.5v13M5.5 12h13"/>',
  'chevron-left': '<path d="M14.5 6 8.5 12l6 6"/>',
  'chevron-right': '<path d="M9.5 6 15.5 12l-6 6"/>',
  'arrow-left': '<path d="M19 12H5"/><path d="M11 18 5 12l6-6"/>',
  trash: '<path d="M5 7h14"/><path d="M9.5 7V5.5A1.5 1.5 0 0 1 11 4h2a1.5 1.5 0 0 1 1.5 1.5V7"/><path d="M6.5 7l.8 11.5a1.5 1.5 0 0 0 1.5 1.4h6.4a1.5 1.5 0 0 0 1.5-1.4L18 7"/>',
  info: '<circle cx="12" cy="12" r="8.5"/><path d="M12 11v5"/><path d="M12 8h.01"/>',
  chat: '<path d="M20 4H4a1.5 1.5 0 0 0-1.5 1.5v9A1.5 1.5 0 0 0 4 16h3v4l5-4h8a1.5 1.5 0 0 0 1.5-1.5v-9A1.5 1.5 0 0 0 20 4Z"/>',
  user: '<circle cx="12" cy="8.5" r="4"/><path d="M4.5 20c0-4 3.5-6.5 7.5-6.5s7.5 2.5 7.5 6.5"/>',
  grid: '<path d="M4.5 4.5h6v6h-6zM13.5 4.5h6v6h-6zM4.5 13.5h6v6h-6zM13.5 13.5h6v6h-6z"/>',
}
</script>

<template>
  <svg
    class="icon" :width="size" :height="size" viewBox="0 0 24 24" fill="none"
    :stroke-width="stroke" stroke="currentColor" stroke-linecap="round" stroke-linejoin="round"
    aria-hidden="true" v-html="ICONS[name] || ''"
  />
</template>

<style scoped>
.icon { display: block; flex-shrink: 0; }
</style>
