"""제품 임베딩 백필 명령.

    python manage.py backfill_embeddings          # 임베딩 없는 제품만
    python manage.py backfill_embeddings --all     # 전체 재생성
    python manage.py backfill_embeddings --batch 30

임베딩은 seed.json에 넣지 않는(재생성 가능한 파생 데이터) 정책이므로, 팀원은 데이터를
loaddata 한 뒤 이 명령으로 벡터를 채운다.
"""
from django.core.management.base import BaseCommand

from chat.embeddings import embed_texts, product_embedding_text
from products.models import Product


class Command(BaseCommand):
    help = '제품 ai_summary 등을 임베딩해 Product.embedding에 채운다 (RAG 검색용).'

    def add_arguments(self, parser):
        parser.add_argument('--batch', type=int, default=50,
                            help='한 번의 GMS 호출에 묶을 제품 수 (기본 50)')
        parser.add_argument('--all', action='store_true',
                            help='이미 임베딩이 있는 제품도 다시 생성')

    def handle(self, *args, **options):
        batch_size = options['batch']
        qs = Product.objects.exclude(ai_summary='')
        if not options['all']:
            qs = qs.filter(embedding__isnull=True)

        products = list(qs)
        total = len(products)
        if total == 0:
            self.stdout.write(self.style.WARNING('백필할 제품이 없습니다.'))
            return

        self.stdout.write(f'임베딩 대상 {total}건 (배치 {batch_size})')

        done = 0
        for start in range(0, total, batch_size):
            chunk = products[start:start + batch_size]
            texts = [product_embedding_text(p) for p in chunk]
            vectors = embed_texts(texts)
            for product, vector in zip(chunk, vectors):
                product.embedding = vector
            Product.objects.bulk_update(chunk, ['embedding'])
            done += len(chunk)
            self.stdout.write(f'  {done}/{total} 완료')

        self.stdout.write(self.style.SUCCESS(f'백필 완료: {done}건'))
