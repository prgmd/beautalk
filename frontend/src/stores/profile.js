import { ref } from 'vue'
import { defineStore } from 'pinia'
import { api } from '@/services/api'

// 백엔드 skin_type은 영문 키, 프론트 UI는 한글 라벨 → 양방향 매핑
const SKIN_TYPE_TO_KO = { dry: '건성', oily: '지성', combination: '복합성', sensitive: '민감성', unknown: '미정' }
const SKIN_TYPE_TO_EN = { 건성: 'dry', 지성: 'oily', 복합성: 'combination', 민감성: 'sensitive', 미정: 'unknown' }

export const useProfileStore = defineStore('profile', () => {
  const skinType = ref('')
  const concerns = ref([])
  const avoidIngredients = ref([])
  const loaded = ref(false) // 백엔드에서 한 번이라도 불러왔는지

  // 로컬 상태만 갱신 (UI 즉시 반영용)
  function update(data) {
    if (data.skinType !== undefined) skinType.value = data.skinType
    if (data.concerns !== undefined) concerns.value = data.concerns
    if (data.avoidIngredients !== undefined) avoidIngredients.value = data.avoidIngredients
  }

  // 백엔드 응답(snake_case, 영문 키) → 프론트 상태(한글)로 반영
  function applyFromServer(d) {
    skinType.value = SKIN_TYPE_TO_KO[d.skin_type] || d.skin_type || ''
    concerns.value = d.concerns || []
    avoidIngredients.value = d.avoid_ingredients || []
  }

  // 프론트 상태 → 백엔드 페이로드(snake_case, 영문 키)
  function toPayload() {
    return {
      skin_type: SKIN_TYPE_TO_EN[skinType.value] || skinType.value,
      concerns: concerns.value,
      avoid_ingredients: avoidIngredients.value,
    }
  }

  // GET /profile — 없으면(204) null 반환
  async function fetchProfile() {
    const { status, data } = await api.get('/profile')
    loaded.value = true
    if (status === 204 || !data) return null
    applyFromServer(data)
    return data
  }

  // 온보딩 최초 저장 (POST는 upsert 처리됨)
  async function saveProfile() {
    const { data } = await api.post('/profile', toPayload())
    if (data) applyFromServer(data)
    return data
  }

  // 마이페이지 수정 (부분 업데이트)
  async function patchProfile(partial) {
    if (partial) update(partial)
    const { data } = await api.patch('/profile', toPayload())
    if (data) applyFromServer(data)
    return data
  }

  return {
    skinType, concerns, avoidIngredients, loaded,
    update, fetchProfile, saveProfile, patchProfile,
  }
})
