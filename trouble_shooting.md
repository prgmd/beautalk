# Troubleshooting

## Problem 1: Cloudflare 403 Blocking
**Issue**: requests 라이브러리로 Olive Young 크롤링 시 403 에러  
**Solution**: 
- undetected_chromedriver 사용 (봇 탐지 우회)
- 버전 명시: `uc.Chrome(version_main=148)`
- URL tracking parameters 추가 (`t_page`, `t_click`)

## Problem 2: JavaScript Rendering
**Issue**: 페이지 로드 후 상품 요소가 없음 (동적 렌더링)  
**Solution**: 
- `WebDriverWait` + `EC.presence_of_all_elements_located()` 사용
- 고정 sleep → 동적 waits로 변경 (최대 15초)

## Problem 3: CSS Selector Changes (styled-components)
**Issue**: 초기 선택자 (`.tx_brand`, `.tx_name`) 존재하지 않음  
**Solution**:
- 브라우저 DevTools로 실제 클래스명 확인
- 정확한 선택자 업데이트:
  - brand: `.TopUtils_btn-brand__tvEdp`
  - name: `.GoodsDetailInfo_title__Vl_IP`
  - price: `.GoodsDetailInfo_price__AoTh8`
  - image: `.Image_image___PUbz img`

## Problem 4: Empty HTML 추출
**Issue**: extract_html.py 실행 시 81줄만 반환  
**Solution**: 
- 페이지 렌더링 완료 대기 필수
- WebDriverWait로 price 요소 로드 확인 후 HTML 추출

## Problem 5: Product 모델 category 필드 누락
**Issue**: 상품 카테고리 저장 불가  
**Solution**:
- models.py에 `category = CharField(max_length=50)` 추가
- `python manage.py makemigrations` → `python manage.py migrate`
