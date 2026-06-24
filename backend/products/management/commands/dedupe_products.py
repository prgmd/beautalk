"""goodsNo 기준 중복 제품을 제거한다.

URL 기준 dedup의 한계로, 같은 제품이 다른 카테고리에서 다른 URL로 재수집되면
중복 행이 생긴다. goodsNo(올리브영 진짜 식별자)로 묶어 대표 1건만 남기고 나머지를
삭제하되, 참조(찜·추천·게시글 태그)는 대표로 재연결해 데이터 유실을 막는다.

    python manage.py dedupe_products           # dry-run (분석만)
    python manage.py dedupe_products --apply    # 실제 삭제·재연결
"""
import collections
from urllib.parse import urlparse, parse_qs

from django.core.management.base import BaseCommand
from django.db import transaction

from products.models import Product, Like
from chat.models import RecommendedProduct


def _goods_no(url: str) -> str:
    return parse_qs(urlparse(url).query).get('goodsNo', [''])[0]


def _rank_key(p):
    """대표 선정 우선순위: 임베딩 보유 > 요약 보유 > 리뷰 많음."""
    return (p.embedding is not None, bool(p.ai_summary), p.review_count or 0)


class Command(BaseCommand):
    help = 'goodsNo 기준 중복 제품 제거 (참조 재연결, 기본 dry-run, 저장 --apply).'

    def add_arguments(self, parser):
        parser.add_argument('--apply', action='store_true', help='실제로 삭제·재연결한다.')

    def handle(self, *args, **options):
        apply = options['apply']

        groups = collections.defaultdict(list)
        for p in Product.objects.all():
            g = _goods_no(p.oliveyoung_url)
            if g:
                groups[g].append(p)

        dup_groups = {g: ps for g, ps in groups.items() if len(ps) > 1}
        if not dup_groups:
            self.stdout.write(self.style.SUCCESS('중복 없음.'))
            return

        total_remove = sum(len(ps) - 1 for ps in dup_groups.values())
        self.stdout.write(f'중복 goodsNo {len(dup_groups)}건 → 제거 대상 {total_remove}건\n')

        # board는 products → board 단방향 의존만 두도록 함수 안에서 import
        from board.models import Post

        removed = 0
        with transaction.atomic():
            for g, ps in dup_groups.items():
                keep, *drops = sorted(ps, key=_rank_key, reverse=True)
                drop_ids = [p.id for p in drops]

                # 참조를 대표로 재연결 (신규 크롤 복사본엔 보통 참조가 없어 0건이지만 안전하게)
                Like.objects.filter(product_id__in=drop_ids).update(product=keep)
                RecommendedProduct.objects.filter(product_id__in=drop_ids).update(product=keep)
                Post.objects.filter(product_id__in=drop_ids).update(product=keep)

                self.stdout.write(f'  [{g}] 유지: {keep.name[:34]}  (-{len(drops)})')
                if apply:
                    for p in drops:
                        p.delete()
                    removed += len(drops)

            if not apply:
                transaction.set_rollback(True)  # dry-run: 재연결도 되돌림

        if apply:
            self.stdout.write(self.style.SUCCESS(f'\n[적용됨] {removed}건 삭제.'))
        else:
            self.stdout.write(self.style.WARNING(
                f'\n[dry-run] {total_remove}건 삭제 예정. 실제 실행은 --apply.'
            ))
