<script setup>
import { onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { useCommunityStore, CATEGORIES } from '@/stores/community'
import { formatRelative } from '@/utils/datetime'
import GlobalSidebar from '@/components/GlobalSidebar.vue'
import Icon from '@/components/Icon.vue'

const router = useRouter()
const community = useCommunityStore()

onMounted(() => {
  community.page = 1
  community.fetchPosts()
})

function selectCategory(key) {
  community.setCategory(key)
}
function openPost(id) {
  router.push(`/community/${id}`)
}
function write() {
  router.push('/community/new')
}
</script>

<template>
  <div class="screen">
    <div class="main">
      <header class="appbar">
        <div>
          <span class="eyebrow">community</span>
          <h1 class="title serif">커뮤니티</h1>
        </div>
        <button class="write-btn" @click="write"><Icon name="plus" :size="16" /> 글쓰기</button>
      </header>

      <!-- 카테고리 필터 -->
      <nav class="filters">
        <button class="chip" :class="{ on: community.category === '' }" @click="selectCategory('')">전체</button>
        <button
          v-for="c in CATEGORIES"
          :key="c.key"
          class="chip"
          :class="{ on: community.category === c.key }"
          @click="selectCategory(c.key)"
        >{{ c.label }}</button>
      </nav>

      <div class="body">
        <p v-if="community.error" class="msg err">{{ community.error }}</p>

        <!-- 스켈레톤 -->
        <ul v-if="community.loading && !community.posts.length" class="list" aria-hidden="true">
          <li v-for="n in 5" :key="n" class="post skel">
            <div class="sk-line sk" style="width:55%" />
            <div class="sk-line sk" style="width:35%; margin-top:12px" />
          </li>
        </ul>

        <ul v-if="community.posts.length" class="list">
          <li
            v-for="(post, i) in community.posts" :key="post.id" class="post"
            :style="{ '--d': i * 30 + 'ms' }"
            role="button" tabindex="0"
            @click="openPost(post.id)"
            @keydown.enter="openPost(post.id)"
            @keydown.space.prevent="openPost(post.id)"
          >
            <div class="post-top">
              <span class="cat" :class="post.category">{{ post.category_label }}</span>
              <span v-if="post.has_product" class="tag-ic" title="제품 태그"><Icon name="tag" :size="13" /></span>
            </div>
            <h2 class="post-title">{{ post.title }}</h2>
            <div class="post-meta">
              <span class="author">{{ post.author }}</span>
              <span class="dot">·</span>
              <span>{{ formatRelative(post.created_at) }}</span>
              <span class="spacer" />
              <span class="stat"><Icon name="chat" :size="13" /> {{ post.comment_count }}</span>
              <span class="stat"><Icon name="heart" :size="13" /> {{ post.like_count }}</span>
            </div>
          </li>
        </ul>

        <div v-if="!community.loading && !community.posts.length && !community.error" class="empty">
          <span class="empty-art"><Icon name="leaf" :size="40" /></span>
          <p class="empty-text">아직 글이 없어요. 첫 글을 남겨보세요.</p>
          <button class="empty-cta" @click="write">글쓰기</button>
        </div>

        <button v-if="community.hasNext" class="more" :disabled="community.loading" @click="community.loadMore()">
          {{ community.loading ? '불러오는 중…' : '더 보기' }}
        </button>
      </div>

      <!-- 모바일 플로팅 글쓰기 버튼 -->
      <button class="fab" @click="write" aria-label="글쓰기"><Icon name="plus" :size="22" /></button>
    </div>

    <GlobalSidebar />
  </div>
</template>

<style scoped>
.screen { height: 100%; display: flex; flex-direction: column; overflow: hidden; }
.main { position: relative; flex: 1; min-height: 0; display: flex; flex-direction: column; overflow: hidden; }

.appbar {
  flex-shrink: 0; display: flex; align-items: flex-end; justify-content: space-between;
  padding: calc(12px + env(safe-area-inset-top)) 20px 6px;
}
.eyebrow { font-size: 10px; letter-spacing: 4px; text-transform: uppercase; color: var(--sage); }
.title { font-size: 26px; font-weight: 500; letter-spacing: -.3px; margin-top: 4px; }
.write-btn {
  display: none; align-items: center; gap: 6px; padding: 9px 16px; border-radius: 99px;
  background: var(--ink); color: var(--canvas); font-size: 13px; font-weight: 600; box-shadow: var(--sh-ink);
  transition: transform var(--t-fast) var(--ease);
}
.write-btn:active { transform: scale(.97); }

.filters {
  flex-shrink: 0; display: flex; gap: 8px; overflow-x: auto;
  padding: 10px 20px 12px; -ms-overflow-style: none; scrollbar-width: none;
}
.filters::-webkit-scrollbar { display: none; }
.chip {
  flex-shrink: 0; padding: 8px 15px; border-radius: 99px; font-size: 13px; font-weight: 600;
  color: var(--ink-soft); background: var(--sheet); border: 1px solid var(--line); transition: all var(--t-fast);
}
.chip:active { transform: scale(.97); }
.chip.on { background: var(--ink); color: var(--canvas); border-color: var(--ink); box-shadow: var(--sh-sm); }

.body { flex: 1; min-height: 0; overflow-y: auto; padding: 6px 20px 90px; }
.msg { font-size: 13px; color: var(--ink-soft); padding: 16px 2px; text-align: center; }
.msg.err { color: var(--danger); }

.list { display: flex; flex-direction: column; gap: 10px; }
.post {
  background: var(--card); border: 1px solid var(--line-soft); border-radius: var(--radius-lg);
  padding: 15px 16px; box-shadow: var(--sh-soft); cursor: pointer;
  animation: card-in .45s var(--ease) both; animation-delay: var(--d, 0ms);
  transition: transform var(--t) var(--ease), box-shadow var(--t) var(--ease), border-color var(--t-fast);
}
.post:hover { transform: translateY(-3px); box-shadow: var(--sh-hover); border-color: var(--line); }
.post-top { display: flex; align-items: center; justify-content: space-between; margin-bottom: 8px; }
.cat {
  font-size: 11px; font-weight: 700; padding: 3px 10px; border-radius: 99px;
  background: var(--sage-soft); color: var(--sage-ink);
}
.cat.qna { background: var(--rose-soft); color: var(--rose-ink); }
.cat.sale { background: #F5E6C8; color: #8A6A2A; }
.tag-ic { display: inline-flex; color: var(--ink-faint); opacity: .85; }
.post-title { font-size: 15.5px; font-weight: 600; line-height: 1.4; letter-spacing: -.2px; color: var(--ink); }
.post-meta {
  display: flex; align-items: center; gap: 6px; margin-top: 9px;
  font-size: 12px; color: var(--ink-faint);
}
.post-meta .author { font-weight: 600; color: var(--ink-soft); }
.post-meta .dot { opacity: .5; }
.post-meta .spacer { flex: 1; }
.post-meta .stat { display: inline-flex; align-items: center; gap: 4px; color: var(--ink-soft); }

/* 스켈레톤 */
.skel { pointer-events: none; animation: none; cursor: default; }
.sk { position: relative; overflow: hidden; background: var(--panel); }
.sk::after {
  content: ''; position: absolute; inset: 0;
  background: linear-gradient(100deg, transparent 20%, rgba(255,255,255,.65) 50%, transparent 80%);
  transform: translateX(-100%); animation: shimmer 1.3s infinite;
}
.sk-line { height: 12px; border-radius: 6px; }

.empty { display: flex; flex-direction: column; align-items: center; gap: 12px; padding: 60px 0; text-align: center; }
.empty-art {
  width: 72px; height: 72px; border-radius: 50%; display: flex; align-items: center; justify-content: center;
  background: var(--sage-soft); color: var(--sage-ink);
}
.empty-text { font-size: 14px; color: var(--ink-soft); }
.empty-cta {
  margin-top: 4px; padding: 11px 24px; border-radius: 99px; background: var(--ink); color: var(--canvas);
  font-size: 13.5px; font-weight: 600; box-shadow: var(--sh-ink);
}

.more {
  display: block; margin: 18px auto 4px; padding: 11px 26px; border-radius: 99px;
  background: var(--card); border: 1px solid var(--line); color: var(--ink-soft); font-size: 13.5px; font-weight: 600;
  box-shadow: var(--sh-sm); transition: all var(--t-fast);
}
.more:hover:not(:disabled) { color: var(--ink); }
.more:disabled { opacity: .5; }

/* 모바일 플로팅 버튼 */
.fab {
  position: absolute; right: 18px; bottom: calc(18px + env(safe-area-inset-bottom));
  width: 54px; height: 54px; border-radius: 50%; background: var(--ink); color: var(--canvas);
  display: flex; align-items: center; justify-content: center;
  line-height: 1; box-shadow: var(--sh-lg); z-index: 4;
  transition: transform var(--t-fast) var(--ease);
}
.fab:active { transform: scale(.93); }

@keyframes card-in { from { opacity: 0; transform: translateY(10px); } to { opacity: 1; transform: none; } }
@keyframes shimmer { 100% { transform: translateX(100%); } }
@media (prefers-reduced-motion: reduce) {
  .post { animation: none; }
  .sk::after { animation: none; }
}

/* ── 데스크탑(≥900px) ── */
@media (min-width: 900px) {
  .screen { flex-direction: row; }
  .appbar, .filters, .body { max-width: 820px; width: 100%; margin-left: auto; margin-right: auto; }
  .appbar { padding: 28px 40px 6px; }
  .filters { padding: 12px 40px 14px; }
  .body { padding: 6px 40px 40px; }
  .title { font-size: 30px; }
  .write-btn { display: inline-flex; }
  .fab { display: none; }
}
</style>
