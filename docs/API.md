# Beautalk API 명세서

## Base URL
```
http://localhost:8000/api/v1
```

## Authentication
JWT Bearer token 사용. Authorization 헤더에 포함:
```
Authorization: Bearer <access_token>
```

---

## OAuth 로그인

### 카카오 로그인 페이지
- **Method**: GET
- **Path**: `/auth/kakao/login/`
- **Description**: 카카오 인증 페이지로 리다이렉트
- **Response**: HTTP 302 redirect to Kakao OAuth URL

### 카카오 로그인 콜백
- **Method**: GET
- **Path**: `/auth/kakao/callback/`
- **Query Parameters**:
  - `code` (string): 카카오 인증 코드
- **Description**: 카카오에서 code를 받아 token 교환 후 프론트엔드로 리다이렉트
- **Response**: HTTP 302 redirect to `http://localhost:5173/auth/callback?access=<token>&refresh=<token>`

### 구글 로그인 페이지
- **Method**: GET
- **Path**: `/auth/google/login/`
- **Description**: 구글 인증 페이지로 리다이렉트
- **Response**: HTTP 302 redirect to Google OAuth URL

### 구글 로그인 콜백
- **Method**: GET
- **Path**: `/auth/google/callback/`
- **Query Parameters**:
  - `code` (string): 구글 인증 코드
- **Description**: 구글에서 code를 받아 token 교환 후 프론트엔드로 리다이렉트
- **Response**: HTTP 302 redirect to `http://localhost:5173/auth/callback?access=<token>&refresh=<token>`

---

## 프로필 API

### 프로필 조회
- **Method**: GET
- **Path**: `/profile`
- **Authentication**: Required
- **Response**:
  ```json
  {
    "skin_type": "dry",
    "concerns": ["acne", "wrinkles"],
    "avoid_ingredients": ["alcohol"],
    "updated_at": "2026-06-22T10:30:00Z"
  }
  ```
  > `id`·`user`는 SkinProfileSerializer `fields`에 미포함 → 응답에 없음.
- **Status**: 200 OK / 204 No Content (프로필 없음)

### 프로필 생성 / 덮어쓰기
- **Method**: POST
- **Path**: `/profile`
- **Authentication**: Required
- **Request Body**:
  ```json
  {
    "skin_type": "dry",
    "concerns": ["acne", "wrinkles"],
    "avoid_ingredients": ["alcohol", "sulfate"]
  }
  ```
- **Response**: 동일 JSON (생성/수정된 프로필)
- **Status**: 201 Created (신규) / 200 OK (기존 프로필 덮어쓰기)
- **Note**: OneToOne 구조라 POST를 여러 번 해도 안전 (upsert 처리)

### 프로필 부분 수정
- **Method**: PATCH
- **Path**: `/profile`
- **Authentication**: Required
- **Request Body**:
  ```json
  {
    "skin_type": "oily"
  }
  ```
- **Response**: 수정된 프로필 JSON
- **Status**: 200 OK
- **Note**: 일부 필드만 수정 가능

---

## JWT 토큰

### 액세스 토큰 발급 (미사용)
- **Method**: POST
- **Path**: `/token/`
- **Description**: username + password 기반 (OAuth 전용 프로젝트라 사용 불가)
- **Status**: 401 Unauthorized (비밀번호 없음)

### 토큰 갱신
- **Method**: POST
- **Path**: `/token/refresh/`
- **Request Body**:
  ```json
  {
    "refresh": "<refresh_token>"
  }
  ```
- **Response**:
  ```json
  {
    "access": "<new_access_token>"
  }
  ```
- **Status**: 200 OK / 401 Unauthorized (토큰 만료)

---

## 에러 응답

### 401 Unauthorized
```json
{
  "detail": "Authentication credentials were not provided."
}
```

### 400 Bad Request
```json
{
  "skin_type": ["Invalid choice."],
  "concerns": ["This field is required."]
}
```

### 404 Not Found
```json
{
  "detail": "Not found."
}
```

---

## 주의사항

### JWT 토큰 전달 방식 (보안 취약)
현재 콜백에서 토큰을 URL 쿼리스트링으로 전달:
```
/auth/callback?access=eyJ...&refresh=eyJ...
```
- ⚠️ 브라우저 히스토리·서버 로그에 노출
- 배포 전 개선 필요 (httpOnly 쿠키 또는 sessionStorage)

### CORS 설정
현재 `http://localhost:5173`만 허용. 배포 시 수정 필요:
```python
# settings.py
CORS_ALLOWED_ORIGINS = [
    'https://yourdomain.com',
]
```

---

## 미구현 API (준비 중)

- [ ] `POST /chat` — 챗봇 메시지
- [ ] `GET /products` — 제품 검색
- [ ] `POST /likes` — 찜하기
- [ ] `GET /recommendations` — 추천 히스토리
