// API 베이스 URL. 배포 환경에선 VITE_API_BASE로 주입(없으면 로컬 기본).
// 예: VITE_API_BASE=https://beautalk.site/api/v1  (frontend/.env.production)
export const API_BASE = import.meta.env.VITE_API_BASE || 'http://localhost:8000/api/v1'
