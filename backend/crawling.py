from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from urllib.parse import urlparse, parse_qs
import undetected_chromedriver as uc
import django
import os
import requests

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()
from products.models import Product, Review

API_HEADERS = {
    "Content-Type": "application/json",
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
}

# API 응답의 answerName을 짧은 표준 단어로 변환
SATISFACTION_MAPPING = {
    "복합성에 좋아요": "복합성",
    "건성에 좋아요": "건성",
    "지성에 좋아요": "지성",
    "민감성에 좋아요": "민감성",
    "보습에 좋아요": "보습",
    "진정에 좋아요": "진정",
    "주름/미백에 좋아요": "주름/미백",
    "세정에 좋아요": "세정",
    "자극없이 순해요": "저자극",
    "보통이에요": "중자극",
}

CATEGORIES = {
    '스킨케어': {'no': '10000010001', 't_click': '%ED%8C%90%EB%A7%A4%EB%9E%AD%ED%82%B9_%EC%8A%A4%ED%82%A8%EC%BC%80%EC%96%B4'},
    '클렌징':   {'no': '10000010010', 't_click': '%ED%8C%90%EB%A7%A4%EB%9E%AD%ED%82%B9_%ED%81%B4%EB%A0%8C%EC%A7%95'},
    '선케어':   {'no': '10000010011', 't_click': '%ED%8C%90%EB%A7%A4%EB%9E%AD%ED%82%B9_%EC%84%A0%EC%BC%80%EC%96%B4'},
    '메이크업': {'no': '10000010002', 't_click': '%ED%8C%90%EB%A7%A4%EB%9E%AD%ED%82%B9_%EB%A9%94%EC%9D%B4%ED%81%AC%EC%97%85'},
}


def get_driver():
    return uc.Chrome(version_main=148)


def get_product_urls(driver, category_no, t_click, top_n=50):
    urls = []
    page = 1

    while len(urls) < top_n:
        print(f'  {page}페이지 크롤링 중...')
        driver.get(
            f'https://www.oliveyoung.co.kr/store/main/getBestList.do'
            f'?dispCatNo=900000100100001&fltDispCatNo={category_no}'
            f'&pageIdx={page}&rowsPerPage=8'
            f'&t_page=%EB%9E%AD%ED%82%B9&t_click={t_click}'
        )

        try:
            WebDriverWait(driver, 15).until(
                EC.presence_of_all_elements_located((By.CSS_SELECTOR, '.cate_prd_list li a.prd_thumb'))
            )
        except Exception as e:
            print(f'    요소 로드 타임아웃: {e}')
            break

        items = driver.find_elements(By.CSS_SELECTOR, '.cate_prd_list li a.prd_thumb')
        if not items:
            break

        for item in items:
            href = item.get_attribute('href')
            if href and href not in urls:
                urls.append(href)

        page += 1

    return urls[:top_n]


def get_satisfaction_from_api(goods_number):
    api_url = f"https://m.oliveyoung.co.kr/review/api/v2/reviews/{goods_number}/stats"

    try:
        response = requests.get(api_url, headers=API_HEADERS, timeout=10)
        if response.status_code == 200:
            data = response.json()
            satisfaction_by_type = {}

            for stat in data.get('data', {}).get('satisfactionStats', []):
                question_name = stat.get('questionName', '')
                answer_dtos = stat.get('answerDtos', [])

                if answer_dtos and question_name:
                    best = max(answer_dtos, key=lambda x: x.get('answerPercentage', 0))
                    answer_name = SATISFACTION_MAPPING.get(best.get('answerName', ''), best.get('answerName', ''))
                    satisfaction_by_type[question_name] = f"{answer_name}: {best.get('answerPercentage', 0)}%"

            return satisfaction_by_type
    except Exception:
        pass

    return {}


def get_reviews_from_api(goods_number, max_reviews=10):
    """유용도순 상위 max_reviews개 리뷰 수집 (커서 기반 페이지네이션)"""
    reviews = []
    api_url = "https://m.oliveyoung.co.kr/review/api/v2/reviews/cursor"
    cursor_id = cursor_score = cursor_count = None

    try:
        while len(reviews) < max_reviews:
            fetch_size = min(50, max_reviews - len(reviews))
            payload = {
                "goodsNumber": goods_number,
                "reviewType": "ALL",
                "sortType": "USEFUL_SCORE_DESC",
                "size": fetch_size,
                "cursorId": cursor_id,
                "cursorScore": cursor_score,
                "cursorCount": cursor_count
            }

            response = requests.post(api_url, json=payload, headers=API_HEADERS)
            if response.status_code != 200:
                print(f'    API 요청 실패: {response.status_code}')
                break

            data = response.json()
            if data.get('status') != 'SUCCESS':
                break

            review_list = data.get('data', {}).get('goodsReviewList', [])
            if not review_list:
                break

            for r in review_list:
                reviews.append({
                    'user_name': r.get('profileDto', {}).get('memberNickname', ''),
                    'rating': r.get('reviewScore', 0),
                    'date': r.get('createdDateTime', ''),
                    'content': r.get('content', ''),
                    'recommend_count': r.get('recommendCount', 0)
                })

            last = review_list[-1]
            cursor_id = last.get('reviewId')
            cursor_score = int(last.get('usefulPoint', 0))
            cursor_count = len(reviews)

            if len(review_list) < fetch_size:
                break

    except Exception as e:
        print(f'    API 리뷰 수집 실패: {e}')

    return reviews


def get_product_detail(driver, url):
    # 리뷰 탭이 처음부터 로드되도록 파라미터 추가
    if 'tab=' not in url:
        url = url + '&tab=review'
    driver.get(url)

    try:
        WebDriverWait(driver, 15).until(
            EC.presence_of_element_located((By.CLASS_NAME, 'GoodsDetailInfo_price__AoTh8'))
        )
    except Exception as e:
        print(f'    요소 로드 타임아웃: {e}')
        return None

    try:
        brand = driver.find_element(By.CSS_SELECTOR, '.TopUtils_btn-brand__tvEdp').text.strip()
        name = driver.find_element(By.CSS_SELECTOR, '.GoodsDetailInfo_title__Vl_IP').text.strip()
        price = int(driver.find_element(By.CSS_SELECTOR, '.GoodsDetailInfo_price__AoTh8').text.strip().replace(',', '').replace('원', ''))
        image_url = driver.find_element(By.CSS_SELECTOR, 'meta[property="og:image"]').get_attribute('content')
    except Exception as e:
        print(f'    파싱 실패: {e}')
        return None

    metadata = {'average_rating': None, 'review_count': 0, 'ai_summary': '', 'satisfaction_by_type': {}}

    # 별점 텍스트 형식: "평점\n4.8"
    try:
        WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.CLASS_NAME, 'rating')))
        rating_text = driver.find_element(By.CLASS_NAME, 'rating').text.strip()
        rating = rating_text.split('\n')[1] if '\n' in rating_text else rating_text.replace('평점', '').strip()
        metadata['average_rating'] = float(rating)
        print(f'    평균 별점: {metadata["average_rating"]}')
    except Exception as e:
        print(f'    평균 별점: 수집 불가 ({e})')

    try:
        review_btn = driver.find_element(By.CSS_SELECTOR, 'button[class*="ReviewArea_btn-review"]')
        count_str = review_btn.find_element(By.TAG_NAME, 'span').text.strip().replace(',', '')
        if count_str.isdigit():
            metadata['review_count'] = int(count_str)
            print(f'    리뷰 개수: {metadata["review_count"]}')
    except Exception:
        print(f'    리뷰 개수: 수집 불가')

    # 올리브영 자체 AI 요약 (feature-item > feature-description)
    try:
        feature_items = driver.find_elements(By.CSS_SELECTOR, 'div.content-wrapper ul.features-list li.feature-item')
        if feature_items:
            metadata['ai_summary'] = feature_items[0].find_element(By.CLASS_NAME, 'feature-description').text.strip()[:500]
            print(f'    AI 요약: {metadata["ai_summary"][:100]}...')
    except Exception:
        pass

    goods_no = parse_qs(urlparse(url).query).get('goodsNo', [''])[0]

    if goods_no:
        api_satisfaction = get_satisfaction_from_api(goods_no)
        if api_satisfaction:
            metadata['satisfaction_by_type'] = api_satisfaction
            for key, value in api_satisfaction.items():
                print(f'    만족도 - {key}: {value}')

        reviews = get_reviews_from_api(goods_no)
        print(f'    리뷰 수집: {len(reviews)}개')
    else:
        print(f'    리뷰 수집: 0개 (goodsNo 추출 실패)')
        reviews = []

    return {
        'brand': brand, 'name': name, 'price': price,
        'oliveyoung_url': url, 'image_url': image_url,
        'average_rating': metadata['average_rating'],
        'review_count': metadata['review_count'],
        'ai_summary': metadata['ai_summary'],
        'satisfaction_by_type': metadata['satisfaction_by_type'],
        'reviews': reviews
    }


def run():
    driver = get_driver()

    # 이미 수집된 URL (tab 파라미터 제거 후 비교)
    existing_urls = set(
        url.split('&tab=')[0]
        for url in Product.objects.values_list('oliveyoung_url', flat=True)
    )
    print(f'기존 제품: {len(existing_urls)}개')

    try:
        for cat_name, cat_info in CATEGORIES.items():
            print(f'[{cat_name}] 크롤링 시작')
            urls = get_product_urls(driver, cat_info['no'], cat_info['t_click'], top_n=50)
            new_urls = [u for u in urls if u.split('&tab=')[0] not in existing_urls]
            print(f'  수집된 URL: {len(urls)}개 (신규: {len(new_urls)}개, 건너뜀: {len(urls) - len(new_urls)}개)')

            for url in new_urls:
                data = get_product_detail(driver, url)
                if data:
                    print(f'  {data["brand"]} {data["name"]} {data["price"]}원')

                    product = Product.objects.create(
                        brand=data['brand'],
                        name=data['name'],
                        price=data['price'],
                        image_url=data['image_url'],
                        oliveyoung_url=data['oliveyoung_url'],
                        category=cat_name,
                        average_rating=data.get('average_rating'),
                        review_count=data.get('review_count', 0),
                        ai_summary=data.get('ai_summary', ''),
                        satisfaction_by_type=data.get('satisfaction_by_type', {}),
                    )
                    existing_urls.add(url.split('&tab=')[0])
                    print(f'    (저장 완료)')

                    reviews = data.get('reviews', [])
                    for r in reviews:
                        Review.objects.create(
                            product=product,
                            text=r.get('content', ''),
                            rating=r.get('rating', 0),
                            user_name=r.get('user_name', ''),
                            recommend_count=r.get('recommend_count', 0),
                            review_date=r.get('date', '')
                        )
                    if reviews:
                        print(f'    리뷰 {len(reviews)}개 저장')
    finally:
        driver.quit()


if __name__ == '__main__':
    run()
