import { ref } from 'vue'
import { defineStore } from 'pinia'

export const useProfileStore = defineStore('profile', () => {
  const skinType = ref('복합성')
  const concerns = ref(['여드름', '모공', '색소침착'])
  const avoidIngredients = ref(['알코올', '파라벤'])

  function update(data) {
    if (data.skinType !== undefined) skinType.value = data.skinType
    if (data.concerns !== undefined) concerns.value = data.concerns
    if (data.avoidIngredients !== undefined) avoidIngredients.value = data.avoidIngredients
  }

  return { skinType, concerns, avoidIngredients, update }
})
