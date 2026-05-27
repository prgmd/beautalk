from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import undetected_chromedriver as uc
import django
import os
import time

# Django 환경을 초기화해야 Product 모델을 찾을 수 있음
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()
from products.models import Product

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

        # JavaScript 렌더링 완료 대기 (최대 15초)
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

def get_product_detail(driver, url):
    driver.get(url)

    # JavaScript 렌더링 완료 대기
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
        price = driver.find_element(By.CSS_SELECTOR, '.GoodsDetailInfo_price__AoTh8').text.strip()
        price = int(price.replace(',', '').replace('원', ''))

        img = driver.find_element(By.CSS_SELECTOR, '.Image_image___PUbz img')
        image_url = img.get_attribute('src')
    except Exception as e:
        print(f'    파싱 실패: {e}')
        return None

    return {
        'brand': brand, 'name': name, 'price': price,
        'oliveyoung_url': url, 'image_url': image_url
    }

def run(test_mode=False):
    driver = get_driver()

    try:
        categories = list(CATEGORIES.items())[:1] if test_mode else CATEGORIES.items()
        top_n = 16 if test_mode else 50

        for cat_name, cat_info in categories:
            print(f'[{cat_name}] 크롤링 시작')
            urls = get_product_urls(driver, cat_info['no'], cat_info['t_click'], top_n=top_n)
            print(f'  수집된 URL: {len(urls)}개')

            for url in urls:
                data = get_product_detail(driver, url)
                if data:
                    print(f'  {data["brand"]} {data["name"]} {data["price"]}원')

                    # 중복 방지하며 DB 저장
                    _, created = Product.objects.update_or_create(
                        oliveyoung_url=data['oliveyoung_url'],
                        defaults={
                            'brand': data['brand'],
                            'name': data['name'],
                            'price': data['price'],
                            'image_url': data['image_url'],
                            'category': cat_name,
                        }
                    )
                    status = '(새로 저장)' if created else '(업데이트)'
                    print(f'    {status}')
    finally:
        driver.quit()

if __name__ == '__main__':
    run(test_mode=True)