"""리뷰 기반으로 ai_summary가 빈 제품의 요약을 LLM으로 생성한다.

크롤러가 올리브영 자체 요약(feature-description)을 못 긁은 제품을 복구한다.
수집된 리뷰(유용도 상위 N개)를 LLM에 주고 제품 특징을 1~2문장으로 요약시킨다.
요약은 RAG 임베딩의 입력이므로, 이게 채워져야 신규 제품이 의미 검색에 잡힌다.

    python manage.py summarize_from_reviews             # 요약 없는 전체
    python manage.py summarize_from_reviews --limit 3   # 테스트로 3개만 (품질 확인)
    python manage.py summarize_from_reviews --reviews 15 # 요약에 쓸 리뷰 수 조정
"""
from django.core.management.base import BaseCommand

from products.models import Product
from chat.views import _call_gms


def _build_summary_prompt(product, review_texts):
    joined = '\n'.join(f'- {t[:200]}' for t in review_texts)
    return [
        {'role': 'system', 'content': (
            '너는 화장품 제품 요약가다. 아래 실제 사용자 리뷰들을 근거로 '
            '제품의 제형·사용감·효과·장점을 1~2문장(120자 이내)으로 객관적으로 요약해라. '
            '과장·이모지·마케팅 문구·인사말 없이 사실 위주로. 반드시 한국어로만 답한다.'
        )},
        {'role': 'user', 'content': (
            f'제품명: {product.brand} {product.name}\n\n[리뷰]\n{joined}\n\n요약:'
        )},
    ]


class Command(BaseCommand):
    help = '리뷰 기반으로 ai_summary가 빈 제품의 요약을 LLM으로 생성한다.'

    def add_arguments(self, parser):
        parser.add_argument('--limit', type=int, default=0, help='처리할 제품 수 상한 (0=전체)')
        parser.add_argument('--reviews', type=int, default=10, help='요약에 쓸 리뷰 수 (기본 10)')

    def handle(self, *args, **options):
        qs = Product.objects.filter(ai_summary='').order_by('name')
        if options['limit']:
            qs = qs[:options['limit']]
        products = list(qs)
        total = len(products)
        if total == 0:
            self.stdout.write(self.style.WARNING('요약 생성할 제품이 없습니다.'))
            return

        self.stdout.write(f'요약 생성 대상 {total}건')
        done = skipped = failed = 0

        for i, p in enumerate(products, 1):
            review_texts = [
                t for t in p.reviews.order_by('-recommend_count')
                .values_list('text', flat=True)[:options['reviews']]
                if t and t.strip()
            ]
            if not review_texts:
                skipped += 1
                self.stdout.write(f'  [{i}/{total}] 리뷰 없음, 건너뜀: {p.name[:30]}')
                continue

            # 요약은 깊은 추론이 불필요 → minimal로 빠르게 (추론 모델일 때만 적용됨)
            content, err = _call_gms(
                _build_summary_prompt(p, review_texts), reasoning_effort='minimal'
            )
            if err or not content:
                failed += 1
                self.stdout.write(self.style.ERROR(f'  [{i}/{total}] 생성 실패: {p.name[:30]}'))
                continue

            p.ai_summary = content.strip()[:500]
            p.save(update_fields=['ai_summary'])
            done += 1
            self.stdout.write(f'  [{i}/{total}] {p.name[:25]} → {p.ai_summary[:50]}')

        self.stdout.write(self.style.SUCCESS(
            f'\n완료: {done}건 생성 / {skipped}건 리뷰없음 / {failed}건 실패'
        ))
