<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useCommunityStore } from '@/stores/community'
import { useAuthStore } from '@/stores/auth'
import { usePostLikesStore } from '@/stores/postLikes'
import { useProductDetailStore } from '@/stores/productDetail'
import { normalizeProduct } from '@/utils/product'
import { formatRelative } from '@/utils/datetime'
import GlobalSidebar from '@/components/GlobalSidebar.vue'

const route = useRoute()
const router = useRouter()
const community = useCommunityStore()
const auth = useAuthStore()
const postLikes = usePostLikesStore()
const productDetail = useProductDetailStore()

const post = ref(null)
const loading = ref(true)
const error = ref('')

// 좋아요는 서버가 현재 사용자 기준 상태를 안 내려줘서 로컬로 토글 표시한다.
// (개수는 서버 응답으로 항상 정확히 갱신)
const liked = ref(false)
const likeCount = ref(0)
const likeBusy = ref(false)

const commentText = ref('')
const commentBusy = ref(false)

// 작성자 표시명 = 이메일 로컬파트(백엔드 _author_name 규칙과 동일). 소유 판별에 사용.
const myName = computed(() => (auth.user?.email ? auth.user.email.split('@')[0] : null))
const isMine = computed(() => post.value && myName.value && post.value.author === myName.value)

async function load() {
  loading.value = true
  error.value = ''
  try {
    if (!auth.user?.email) await auth.fetchAccount().catch(() => {})
    const data = await community.fetchPost(route.params.id)
    post.value = data
    likeCount.value = data?.like_count || 0
    // 서버가 is_liked를 주면 우선 사용, 없으면 로컬 기억으로 복원
    liked.value = data?.is_liked != null ? data.is_liked : postLikes.isLiked(data.id)
  } catch (e) {
    error.value = e?.status === 404 ? '삭제되었거나 존재하지 않는 글이에요.' : '글을 불러오지 못했어요.'
  } finally {
    loading.value = false
  }
}

async function toggleLike() {
  if (likeBusy.value || !post.value) return
  likeBusy.value = true
  try {
    const res = liked.value
      ? await community.unlike(post.value.id)
      : await community.like(post.value.id)
    liked.value = res.liked
    likeCount.value = res.like_count
    postLikes.set(post.value.id, res.liked) // 로컬에 좋아요 상태 기억

  } catch {
    /* 무시 — 다음 시도에서 복구 */
  } finally {
    likeBusy.value = false
  }
}

async function submitComment() {
  const text = commentText.value.trim()
  if (!text || commentBusy.value) return
  commentBusy.value = true
  try {
    const c = await community.addComment(post.value.id, text)
    post.value.comments.push(c)
    commentText.value = ''
  } catch {
    /* 무시 */
  } finally {
    commentBusy.value = false
  }
}

async function removeComment(id) {
  if (!confirm('댓글을 삭제할까요?')) return
  try {
    await community.deleteComment(id)
    post.value.comments = post.value.comments.filter((c) => c.id !== id)
  } catch {
    /* 무시 */
  }
}

async function removePost() {
  if (!confirm('이 글을 삭제할까요? 되돌릴 수 없어요.')) return
  try {
    await community.deletePost(post.value.id)
    router.replace('/community')
  } catch {
    error.value = '삭제에 실패했어요.'
  }
}

function editPost() {
  router.push(`/community/${post.value.id}/edit`)
}

function openProduct() {
  if (post.value?.product) productDetail.open(normalizeProduct(post.value.product))
}

function back() {
  router.push('/community')
}

onMounted(load)
</script>

<template>
  <div class="screen">
    <div class="main">
      <header class="topbar">
        <button class="back" @click="back" aria-label="뒤로">‹</button>
        <span class="topbar-title">게시글</span>
        <div v-if="isMine" class="owner-actions">
          <button class="oa" @click="editPost">수정</button>
          <button class="oa danger" @click="removePost">삭제</button>
        </div>
        <span v-else class="oa-spacer" />
      </header>

      <div class="body">
        <p v-if="loading" class="msg">불러오는 중...</p>
        <p v-else-if="error" class="msg err">{{ error }}</p>

        <article v-else-if="post" class="article">
          <span class="cat" :class="post.category">{{ post.category_label }}</span>
          <h1 class="title">{{ post.title }}</h1>
          <div class="meta">
            <span class="author">{{ post.author }}</span>
            <span class="dot">·</span>
            <span>{{ formatRelative(post.created_at) }}</span>
          </div>

          <div class="content">{{ post.content }}</div>

          <!-- 태그된 제품 -->
          <button v-if="post.product" class="product-card" @click="openProduct">
            <div class="pc-img">
              <img v-if="post.product.image_url || post.product.image" :src="post.product.image_url || post.product.image" :alt="post.product.name" />
              <span v-else class="pc-ph">🧴</span>
            </div>
            <div class="pc-meta">
              <span class="pc-tag">🏷 태그된 제품</span>
              <p class="pc-brand">{{ post.product.brand }}</p>
              <p class="pc-name">{{ post.product.name }}</p>
            </div>
            <span class="pc-arrow">›</span>
          </button>

          <!-- 좋아요 -->
          <div class="like-row">
            <button class="like-btn" :class="{ on: liked }" :disabled="likeBusy" @click="toggleLike">
              <span class="lh">{{ liked ? '♥' : '♡' }}</span> 좋아요 {{ likeCount }}
            </button>
          </div>

          <!-- 댓글 -->
          <section class="comments">
            <h2 class="c-head">댓글 <span class="c-count">{{ post.comments.length }}</span></h2>

            <ul v-if="post.comments.length" class="c-list">
              <li v-for="c in post.comments" :key="c.id" class="c-item">
                <div class="c-top">
                  <span class="c-author">{{ c.author }}</span>
                  <span class="c-date">{{ formatRelative(c.created_at) }}</span>
                  <button
                    v-if="myName && c.author === myName"
                    class="c-del" @click="removeComment(c.id)" aria-label="댓글 삭제"
                  >×</button>
                </div>
                <p class="c-text">{{ c.content }}</p>
              </li>
            </ul>
            <p v-else class="c-empty">첫 댓글을 남겨보세요.</p>
          </section>
        </article>
      </div>

      <!-- 댓글 입력 -->
      <div v-if="post" class="composer">
        <input
          v-model="commentText"
          placeholder="댓글을 입력하세요"
          maxlength="500"
          @keyup.enter="submitComment"
        />
        <button class="c-send" :disabled="!commentText.trim() || commentBusy" @click="submitComment">등록</button>
      </div>
    </div>

    <GlobalSidebar />
  </div>
</template>

<style scoped>
.screen { height: 100%; display: flex; flex-direction: column; overflow: hidden; }
.main { flex: 1; min-height: 0; display: flex; flex-direction: column; overflow: hidden; }

.topbar {
  flex-shrink: 0; display: flex; align-items: center; gap: 8px;
  padding: calc(10px + env(safe-area-inset-top)) 12px 10px; border-bottom: 1px solid var(--line-soft);
}
.back { width: 36px; height: 36px; font-size: 24px; color: var(--ink); display: flex; align-items: center; justify-content: center; }
.topbar-title { font-size: 15px; font-weight: 600; color: var(--ink); }
.owner-actions { margin-left: auto; display: flex; gap: 4px; }
.oa-spacer { margin-left: auto; }
.oa { padding: 7px 12px; font-size: 13px; font-weight: 600; color: var(--ink-soft); border-radius: var(--radius-sm); }
.oa:hover { background: var(--panel); color: var(--ink); }
.oa.danger { color: var(--danger); }

.body { flex: 1; min-height: 0; overflow-y: auto; padding: 18px 20px 24px; }
.msg { font-size: 13px; color: var(--ink-soft); padding: 30px 2px; text-align: center; }
.msg.err { color: var(--danger); }

.cat {
  display: inline-block; font-size: 11px; font-weight: 700; padding: 4px 11px; border-radius: 99px;
  background: var(--sage-soft); color: var(--sage-ink);
}
.cat.qna { background: var(--rose-soft); color: var(--rose-ink); }
.cat.sale { background: #F5E6C8; color: #8A6A2A; }
.title { font-size: 22px; font-weight: 600; line-height: 1.35; letter-spacing: -.3px; margin: 12px 0 8px; color: var(--ink); }
.meta { display: flex; align-items: center; gap: 6px; font-size: 12.5px; color: var(--ink-faint); }
.meta .author { font-weight: 600; color: var(--ink-soft); }
.meta .dot { opacity: .5; }

.content {
  margin: 20px 0 22px; font-size: 14.5px; line-height: 1.78; color: var(--ink); white-space: pre-line;
}

.product-card {
  width: 100%; display: flex; align-items: center; gap: 13px; text-align: left;
  padding: 12px; border-radius: var(--radius-lg); background: var(--sheet); border: 1px solid var(--line);
  box-shadow: var(--sh-sm); transition: transform var(--t-fast) var(--ease), box-shadow var(--t-fast);
}
.product-card:hover { transform: translateY(-2px); box-shadow: var(--sh-md); }
.pc-img {
  width: 56px; height: 56px; flex-shrink: 0; border-radius: 12px; overflow: hidden;
  background: linear-gradient(170deg,#EFE7DB,#DEE7DF); display: flex; align-items: center; justify-content: center;
}
.pc-img img { width: 100%; height: 100%; object-fit: cover; }
.pc-ph { font-size: 26px; }
.pc-meta { flex: 1; min-width: 0; }
.pc-tag { font-size: 10.5px; font-weight: 700; color: var(--sage); }
.pc-brand { font-size: 11px; letter-spacing: 1px; text-transform: uppercase; color: var(--ink-faint); margin-top: 3px; }
.pc-name { font-size: 13.5px; font-weight: 600; color: var(--ink); line-height: 1.3; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
.pc-arrow { font-size: 22px; color: var(--ink-faint); flex-shrink: 0; }

.like-row { margin: 22px 0; display: flex; justify-content: center; }
.like-btn {
  display: inline-flex; align-items: center; gap: 8px; padding: 11px 24px; border-radius: 99px;
  background: var(--card); border: 1px solid var(--line); color: var(--ink-soft); font-size: 14px; font-weight: 600;
  box-shadow: var(--sh-sm); transition: all var(--t-fast) var(--ease);
}
.like-btn:active { transform: scale(.97); }
.like-btn .lh { font-size: 15px; color: var(--rose); }
.like-btn.on { background: var(--rose-soft); border-color: transparent; color: var(--rose-ink); }
.like-btn.on .lh { color: var(--rose); }

.comments { border-top: 1px solid var(--line-soft); padding-top: 20px; }
.c-head { font-size: 14px; font-weight: 700; color: var(--ink); margin-bottom: 14px; }
.c-count { color: var(--sage); }
.c-list { display: flex; flex-direction: column; gap: 16px; }
.c-item { }
.c-top { display: flex; align-items: center; gap: 8px; }
.c-author { font-size: 12.5px; font-weight: 600; color: var(--ink); }
.c-date { font-size: 11.5px; color: var(--ink-faint); }
.c-del { margin-left: auto; width: 22px; height: 22px; border-radius: 50%; color: var(--ink-faint); font-size: 15px; }
.c-del:hover { background: var(--danger-bg); color: var(--danger); }
.c-text { margin-top: 5px; font-size: 14px; line-height: 1.6; color: var(--ink-soft); white-space: pre-line; }
.c-empty { font-size: 13px; color: var(--ink-faint); padding: 8px 0; }

.composer {
  flex-shrink: 0; display: flex; gap: 8px; align-items: center;
  padding: 10px 16px calc(10px + env(safe-area-inset-bottom)); border-top: 1px solid var(--line-soft); background: var(--sheet);
}
.composer input {
  flex: 1; min-width: 0; padding: 12px 15px; border: 1px solid var(--line); border-radius: 99px;
  font-size: 14px; background: var(--card); color: var(--ink); outline: none;
  transition: border-color var(--t-fast), box-shadow var(--t-fast);
}
.composer input:focus { border-color: var(--sage); box-shadow: 0 0 0 3px rgba(126,139,109,.15); }
.c-send {
  flex-shrink: 0; padding: 12px 18px; border-radius: 99px; background: var(--ink); color: var(--canvas);
  font-size: 13.5px; font-weight: 600; box-shadow: var(--sh-ink); transition: opacity var(--t-fast);
}
.c-send:disabled { opacity: .4; }

/* ── 데스크탑(≥900px) ── */
@media (min-width: 900px) {
  .screen { flex-direction: row; }
  .topbar, .body, .composer { max-width: 760px; width: 100%; margin-left: auto; margin-right: auto; }
  .topbar { padding: 24px 40px 14px; }
  .body { padding: 26px 40px 30px; }
  .title { font-size: 27px; }
  .composer { padding: 12px 40px 20px; }
}
</style>
