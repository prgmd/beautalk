import leaf from '@/assets/avatars/leaf.svg'
import blossom from '@/assets/avatars/blossom.svg'
import sprig from '@/assets/avatars/sprig.svg'
import monstera from '@/assets/avatars/monstera.svg'

// 고를 수 있는 프로필 사진 4종(식물 테마, 브랜드 톤)
export const AVATARS = [
  { key: 'leaf', label: '잎', src: leaf },
  { key: 'blossom', label: '꽃', src: blossom },
  { key: 'sprig', label: '새싹', src: sprig },
  { key: 'monstera', label: '몬스테라', src: monstera },
]

export function avatarSrc(key) {
  return AVATARS.find((a) => a.key === key)?.src || null
}
