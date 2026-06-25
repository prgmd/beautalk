"""추천 품질 자동 평가 — "추천이 조건을 지키는지"를 감이 아니라 숫자로 검증한다.

대표 쿼리들을 **실제 하이브리드 추천의 SQL 필터 층**(_resolve_constraints + _apply_degradation)에
통과시켜, 후보 풀이 사용자의 원래 조건(제형·가격)을 얼마나 충족하는지 측정한다.

핵심 주장의 증명:
  - **완화가 일어나지 않은 쿼리는 조건 충족률 100%** — SQL이 위반 제품을 후보에서 통째로 빼므로,
    LLM은 조건 위반 제품을 '볼 수조차 없다'(구조적 보장).
  - 후보가 부족해 완화한 경우는 '무엇을 풀었는지'가 그대로 드러난다(정직성).

LLM(임베딩·생성) 호출 없이 결정론적 SQL만 평가하므로 **빠르고 재현 가능**하다.
실행: python manage.py eval_recommend
"""

from django.core.management.base import BaseCommand

from products.models import Product
from chat.views import _resolve_constraints, _apply_degradation, RECOMMEND_POOL_SIZE
from chat.serializers import product_meets


# 대표 평가 쿼리 — (라벨, 사용자 발화). 제형·가격 조합을 폭넓게 덮는다.
# 발화는 실제 제약 추출기(_resolve_constraints)가 파싱하는 자연어 그대로 둔다.
EVAL_QUERIES = [
    ('지성·2~3만원·로션', '지성 피부인데 2~3만원대 로션 추천해줘'),
    ('건성·3만원이하·크림', '건조한 피부에 3만원 이하 크림 찾아줘'),
    ('선크림',            '끈적이지 않는 선크림 추천해줘'),
    ('클렌저·1~2만원',    '1~2만원대 순한 클렌저 있어?'),
    ('토너·2만원이하',    '2만원 이하 토너 추천'),
    ('세럼·2~3만원',      '2~3만원대 세럼 추천해줘'),
    ('미스트·1만원이하',  '1만원 이하 미스트 찾아줘'),
    ('패드·2~3만원',      '2~3만원대 패드 추천'),
    ('마스크팩',          '진정되는 마스크팩 추천해줘'),
    ('에센스·3~5만원',    '3~5만원대 에센스 추천'),
    ('로션·1만원이하',    '1만원 이하 로션 있을까?'),
    ('크림·5만원이상',    '5만원 이상 고급 크림 추천해줘'),
    ('선크림·2만원이하',  '2만원 이하 선크림 추천'),
    ('세럼',             '여드름 자국에 좋은 세럼 추천해줘'),
    ('클렌저·1만원이하',  '1만원 이하 클렌저 찾아줘'),
]


class Command(BaseCommand):
    help = '대표 쿼리로 추천 조건 충족률을 측정한다(LLM 호출 없음).'

    def handle(self, *args, **options):
        base = Product.objects.exclude(ai_summary='')

        rows = []
        # 누적 집계 — 완화 전(=완화 안 일어난 쿼리)과 전체를 분리해 본다.
        agg = {
            'form_ok': 0, 'form_total': 0,
            'price_ok': 0, 'price_total': 0,
            'relaxed_count': 0,
            'no_relax_form_ok': 0, 'no_relax_form_total': 0,
            'no_relax_price_ok': 0, 'no_relax_price_total': 0,
        }

        for label, utterance in EVAL_QUERIES:
            history = [{'role': 'user', 'content': utterance}]
            requested = _resolve_constraints(history, None)
            qs, applied, relaxed_axes = _apply_degradation(base, requested)
            pool = list(qs[:RECOMMEND_POOL_SIZE])

            form_total = price_total = form_ok = price_ok = 0
            for p in pool:
                meets = product_meets(p, requested)
                if 'form' in meets:
                    form_total += 1
                    form_ok += 1 if meets['form'] else 0
                if 'price' in meets:
                    price_total += 1
                    price_ok += 1 if meets['price'] else 0

            relaxed = bool(relaxed_axes)
            rows.append({
                'label': label, 'n': len(pool), 'relaxed': relaxed_axes,
                'form': (form_ok, form_total), 'price': (price_ok, price_total),
            })

            agg['form_ok'] += form_ok; agg['form_total'] += form_total
            agg['price_ok'] += price_ok; agg['price_total'] += price_total
            agg['relaxed_count'] += 1 if relaxed else 0
            if not relaxed:
                agg['no_relax_form_ok'] += form_ok; agg['no_relax_form_total'] += form_total
                agg['no_relax_price_ok'] += price_ok; agg['no_relax_price_total'] += price_total

        # ── 출력 ──
        def pct(ok, total):
            return f'{(100 * ok / total):.0f}%' if total else '  -'

        self.stdout.write('')
        self.stdout.write(self.style.MIGRATE_HEADING('추천 조건 충족률 평가 (SQL 필터 층, LLM 미호출)'))
        self.stdout.write('-' * 64)
        self.stdout.write(f'{"쿼리":<20}{"후보":>4}  {"제형":>6}  {"가격":>6}  완화')
        self.stdout.write('-' * 64)
        for r in rows:
            relax = '·'.join(r['relaxed']) if r['relaxed'] else '—'
            self.stdout.write(
                f'{r["label"]:<20}{r["n"]:>4}  '
                f'{pct(*r["form"]):>6}  {pct(*r["price"]):>6}  {relax}'
            )
        self.stdout.write('-' * 64)

        n = len(EVAL_QUERIES)
        self.stdout.write('')
        self.stdout.write(self.style.SUCCESS('[전체]'))
        self.stdout.write(f'  제형 충족률: {pct(agg["form_ok"], agg["form_total"])}'
                          f'   가격 충족률: {pct(agg["price_ok"], agg["price_total"])}')
        self.stdout.write(f'  완화 발생: {agg["relaxed_count"]}/{n} 쿼리')
        self.stdout.write('')
        self.stdout.write(self.style.SUCCESS('[완화가 일어나지 않은 쿼리 — 구조적 보장 구간]'))
        self.stdout.write(f'  제형 충족률: {pct(agg["no_relax_form_ok"], agg["no_relax_form_total"])}'
                          f'   가격 충족률: {pct(agg["no_relax_price_ok"], agg["no_relax_price_total"])}')
        self.stdout.write('  → 완화 없이 추천되는 후보는 항상 원래 조건을 만족한다(SQL이 위반 제품을 통째로 제외).')
        self.stdout.write('')
