// API 베이스 URL. 배포 환경에선 VITE_API_ORIGIN으로 주입(없으면 로컬 기본).
export const API_ORIGIN = import.meta.env.VITE_API_ORIGIN || 'http://localhost:8000'
export const API_BASE = `${API_ORIGIN}/api/v1`
