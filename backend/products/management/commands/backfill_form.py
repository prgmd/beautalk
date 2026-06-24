"""제품명 규칙 파싱으로 Product.form(제형, 복수 가능)을 백필한다.

하이브리드 추천의 SQL 필터 축인 `form`을 채운다. LLM 없이 결정론적 규칙으로:
  1) `[...]` 마케팅 브라켓과 `(...)` 사은품 구문을 제거한다(다른 제형이 섞여 오매칭 방지).
  2) 공백 제거 + 소문자화로 "선 크림"·"H2O" 같은 표기 변형을 흡수한다.
  3) **배타 제형**(suncream·cleanser): 그 자체로 단일 제형이라 매칭되면 즉시 단독 반환한다.
     "선세럼"=suncream(serum 아님), "딥 클렌징 포밍 크림"=cleanser(cream 아님)를 보장.
  4) **가산 제형**(toner·lotion·…): 류온오프 제품은 한 제품이 여러 제형일 수 있어
     매칭되는 것을 모두 수집한다. "크림앤세럼"=[cream, serum], "스킨로션"=[toner, lotion].
  5) 아무것도 못 잡으면 카테고리 폴백(선케어→suncream, 클렌징→cleanser).

기본은 dry-run(분류 결과만 출력). 실제 저장은 --apply.
"""

import re

from django.core.management.base import BaseCommand

from products.models import Product

# 배타 제형 — 매칭되면 그것만 반환(텍스처어 '크림/세럼'은 수식어일 뿐).
# suncream을 먼저 봐서 "선세럼/선크림"이 serum/cream으로 새지 않게 한다.
EXCLUSIVE_RULES = [
    ('suncream', ['선크림', '썬크림', '선세럼', '썬세럼', '선에센스', '선로션',
                  '선토너', '선밤', '선젤', '선스틱', '썬스틱', '선스프레이',
                  '선스크린', '썬스크린']),
    ('cleanser', ['클렌징', '클렌저', '클렌즈', '클린잇', '포밍클렌', '미셀라', 'h2o']),
]

# 가산 제형 — 매칭되는 것을 모두 수집(한 제품이 여러 제형일 수 있음).
ADDITIVE_RULES = [
    ('pad', ['패드']),
    ('mask', ['마스크', '시트팩', '시트마스크']),
    ('mist', ['미스트']),
    ('cream', ['크림']),
    ('serum', ['세럼', '앰플']),
    ('essence', ['에센스']),
    ('lotion', ['로션', '에멀전', '유액', '밀크']),
    ('toner', ['토너', '스킨']),
]

# 이름으로 못 잡았을 때의 카테고리 폴백(해당 카테고리는 사실상 단일 제형).
CATEGORY_FALLBACK = {
    '선케어': 'suncream',
    '클렌징': 'cleanser',
}


def _normalize(name: str) -> str:
    """`[...]`·`(...)` 제거 + 공백 제거 + 소문자화한 매칭용 문자열."""
    name = re.sub(r'\[[^\]]*\]', '', name)   # [마케팅 문구] 제거
    name = re.sub(r'\([^)]*\)', '', name)    # (사은품/구성) 제거
    return name.replace(' ', '').lower()


def classify(product) -> list:
    """제품 1건의 form 키 리스트를 반환한다. 미분류는 빈 리스트([])."""
    text = _normalize(product.name)

    # 1) 배타 제형: 매칭되면 단독 반환.
    for form, keywords in EXCLUSIVE_RULES:
        if any(kw in text for kw in keywords):
            return [form]

    # 2) 가산 제형: 매칭되는 것 모두 수집.
    forms = [form for form, keywords in ADDITIVE_RULES
             if any(kw in text for kw in keywords)]
    if forms:
        return forms

    # 3) 카테고리 폴백.
    fallback = CATEGORY_FALLBACK.get(product.category)
    return [fallback] if fallback else []


class Command(BaseCommand):
    help = '제품명 규칙 파싱으로 Product.form(복수 가능)을 백필한다 (기본 dry-run, 저장은 --apply).'

    def add_arguments(self, parser):
        parser.add_argument(
            '--apply', action='store_true',
            help='실제로 DB에 저장한다 (없으면 분류 결과만 출력하는 dry-run).',
        )

    def handle(self, *args, **options):
        apply = options['apply']
        valid_forms = {k for k, _ in Product.FORM_CHOICES}

        per_form = {}        # 제형별 등장 횟수(한 제품이 여러 제형이면 각각 +1)
        multi = []           # 복수 제형 제품(검수)
        unclassified = []    # 미분류 제품(검수)
        to_update = []

        for product in Product.objects.all():
            forms = classify(product)

            bad = [f for f in forms if f not in valid_forms]
            if bad:
                # 규칙이 enum 밖 키를 내면 코드 버그 — 조용히 넘기지 말고 드러낸다.
                self.stderr.write(f'잘못된 form 키 {bad} (규칙 점검 필요): {product.name}')
                forms = [f for f in forms if f in valid_forms]

            for f in forms:
                per_form[f] = per_form.get(f, 0) + 1
            if len(forms) >= 2:
                multi.append(f'{forms} | {product.name}')
            if not forms:
                unclassified.append(f'[{product.category}] {product.name}')

            if product.form != forms:
                product.form = forms
                to_update.append(product)

        # 제형별 분포
        self.stdout.write('\n=== 제형별 분포 (제품이 복수면 중복 계수) ===')
        for form in sorted(per_form, key=lambda k: -per_form[k]):
            self.stdout.write(f'  {form:12} {per_form[form]:3}건')

        # 복수 제형 제품(검수)
        if multi:
            self.stdout.write(f'\n=== 복수 제형 {len(multi)}건 (검수) ===')
            for line in multi:
                self.stdout.write(f'  {line}')

        # 미분류(검수)
        if unclassified:
            self.stdout.write(f'\n=== 미분류 {len(unclassified)}건 (검수) ===')
            for line in unclassified:
                self.stdout.write(f'  {line}')

        # 적용
        if apply:
            if to_update:
                Product.objects.bulk_update(to_update, ['form'])
            self.stdout.write(self.style.SUCCESS(f'\n[적용됨] {len(to_update)}건 form 갱신.'))
        else:
            self.stdout.write(self.style.WARNING(
                f'\n[dry-run] {len(to_update)}건이 갱신 대상. 실제 저장하려면 --apply.'
            ))
