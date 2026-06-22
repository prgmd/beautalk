# 코드 전수 리뷰 결과 (2026-06-22)

프론트/백엔드/계약 3개 영역을 정밀 리뷰한 결과. 프론트 확정 버그는 이 PR에서 수정,
백엔드 항목은 담당 팀원 인계용으로 정리한다.

---

## ✅ 이 PR에서 수정한 것 (프론트)

| 항목 | 파일 | 내용 |
|------|------|------|
| 찜 목록 가격 크래시 | `LikedProductsView.vue` | `formatPrice`가 `?.` 누락 → price가 null인 항목에서 그리드 전체가 깨지던 것 수정 |
| 찜 목록 이미지 미표시 | `LikedProductsView.vue` | 항상 🧴 placeholder만 그리던 것 → 실제 `product.image` 표시(추천 화면과 일관) |
| 추천 날짜 방어 | `RecommendedProductsView.vue` | `formatDate`에 Invalid Date 가드 추가 |
| 별점 렌더 방어 | `ProductDetailModal.vue` | `stars()`에 0~5 클램프 + 숫자 변환 가드(비정상 rating에 `repeat` 크래시 방지) |
| 죽은 스캐폴드 제거 | `HomeView/AboutView/TheWelcome/WelcomeItem/HelloWorld/icons*/counter.js` | 라우터·어디서도 참조 없는 Vue 스캐폴드 11개 삭제 |

## 🟡 프론트 — 보류(선택, 데모 영향 적음)
- `toggleLike` 실패가 `console.warn`만 → 사용자 피드백 없음. 토스트 시스템 없어서 보류(낙관적 롤백은 동작).
- App.vue 시작 시 refresh와 api.js `tryRefresh`가 별도 fetch라 시작 시 refresh POST가 드물게 2번 날 수 있음(저영향).
- 라우터에 `hasProfile` 가드 없음 → 프로필 없이 `/chat` 직접 진입 가능. 단 백엔드가 프로필 미입력을 정상 처리하므로 의도된 동작일 수 있음.
- 클릭 가능한 `div`들 키보드 접근성 미흡(`role`/`tabindex` 없음).
- `GET /products/`·`/products/<id>/` API는 프론트에서 미사용(제품 상세는 추천 payload + 목업 리뷰로 처리 중).

---

## ➡️ 백엔드 인계 (담당 팀원)

### High
- **H1. `DEBUG = True` 하드코딩** (`config/settings.py:12`) — 배포 시 트레이스백 노출. env로 분리.
- **H2. `ALLOWED_HOSTS = []`** (`config/settings.py:14`) — DEBUG 끄는 순간 전 요청 400. env로.
- **H3. 추천 프롬프트가 여전히 전 제품 주입** (`chat/views.py:172`) — `_build_recommend_prompt`가 ai_summary 보유 제품 **전부**(~27k자)를 넣어 GMS가 "400 Model not found"로 거부하는 그 원인이 **아직 미수정**. `[:N]` 슬라이스 + ai_summary 길이 컷 필요. (검증: 15개로 줄이면 200 정상)
- **H4. LLM 엔드포인트 전용 throttle 없음** — `/chat`·`/recommend`(유료 GMS 호출)가 전역 100/day만 적용. `ScopedRateThrottle` 권장.

### Medium
- **M1.** refresh 쿠키 `Secure` 미설정 (`accounts/views.py:32`) — 운영 HTTP 전송 위험. `secure=not DEBUG`.
- **M2.** OAuth redirect_uri·프론트 URL이 localhost 하드코딩 (`accounts/views.py` 다수) — 배포 시 OAuth 교환 실패. env로.
- **M3.** GMS 응답 파싱 무방비 (`chat/views.py:72`) — `['choices'][0]...`가 예상외 200 페이로드에 KeyError/500. try/except로 502 처리.
- **M4.** 추천 결과 3개 상한 미적용 (`chat/views.py:236`) — LLM이 >3개 줘도 그대로 저장. `matched[:3]`.
- **M5.** `_skin_block`이 `UserInfo` 없는 User에서 500 (`chat/views.py:35`) — `UserInfo.DoesNotExist`도 가드.
- **M6.** 프로덕션 경로에 `print(...)` 디버그 로그 (`chat/views.py:230`) → `logging`으로.

### Low
- 추천 히스토리/찜 목록 APIView 페이지네이션 없음(`PAGE_SIZE` 미적용).
- `unique_ln_use` 오타(→ `unique_in_use`), 모델 `Meta.ordering`/인덱스 부재 등.
- `ROTATE_REFRESH_TOKENS`/`BLACKLIST_AFTER_ROTATION` 설정이 커스텀 refresh 뷰에선 사실상 무효(저영향, by-design).

> 계약(프론트↔백엔드)은 전수 대조 결과 **불일치 없음** — 모든 프론트 호출이 실제 라우트(메서드·경로·슬래시)와 일치하고, 필드명도 정규화로 맞음.
