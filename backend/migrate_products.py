import sqlite3
import sys

# UTF-8 설정
if sys.stdout.encoding != 'utf-8':
    sys.stdout.reconfigure(encoding='utf-8')

# 구 DB와 새 DB 연결
old_db = sqlite3.connect(r'..\old_db\db.sqlite3')
new_db = sqlite3.connect('db.sqlite3')

old_cursor = old_db.cursor()
new_cursor = new_db.cursor()

# 1. 구 DB에서 Product 데이터 모두 가져오기
old_cursor.execute("SELECT * FROM products_product")
products = old_cursor.fetchall()
print(f"[OK] Old DB: {len(products)} products loaded")

# 2. 새 DB의 기존 products_product 데이터 삭제
new_cursor.execute("DELETE FROM products_product")
new_db.commit()
print(f"[OK] New DB products table cleared")

# 3. 구 DB 데이터를 새 DB에 삽입
new_cursor.executemany(
    """INSERT INTO products_product
    (id, brand, name, price, oliveyoung_url, image_url, category, ai_summary, average_rating, review_count, satisfaction_by_type)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
    products
)
new_db.commit()
print(f"[OK] New DB: {len(products)} products inserted")

# 4. 검증
new_cursor.execute("SELECT COUNT(*) FROM products_product")
count = new_cursor.fetchone()[0]
print(f"[OK] Verification: {count} products in new DB")

old_db.close()
new_db.close()
