"""GMS 임베딩 호출 모듈.

추천 RAG에서 (1) 제품 텍스트를 벡터로 백필하고 (2) 사용자 대화를 벡터로 변환해
유사 제품을 검색하는 데 쓰인다. GMS는 OpenAI 호환 프록시라 embeddings 엔드포인트도
chat/completions와 같은 베이스 URL 아래에 있다.
"""
import json
import logging
import os

import requests as http

from .observability import traceable

logger = logging.getLogger(__name__)

# GMS_API_URL은 .../chat/completions 를 가리키므로 같은 베이스의 /embeddings 로 치환한다.
_CHAT_URL = os.environ.get(
    'GMS_API_URL', 'https://gms.ssafy.io/gmsapi/api.openai.com/v1/chat/completions'
)
GMS_EMBED_URL = _CHAT_URL.replace('/chat/completions', '/embeddings')
GMS_API_KEY = os.environ.get('GMS_API_KEY')
EMBED_MODEL = os.environ.get('GMS_EMBED_MODEL', 'text-embedding-3-small')
EMBED_DIM = 1536


@traceable(name='embed')
def embed_texts(texts, *, timeout=60):
    """여러 텍스트를 한 번에 임베딩한다. OpenAI embeddings는 input 배열을 지원하므로
    제품 N개를 한 번의 호출로 처리할 수 있다(백필 효율).

    반환: 입력 순서와 동일한 벡터 리스트(list[list[float]]).
    실패 시 예외를 그대로 올린다(호출 측에서 폴백 처리).
    """
    if not texts:
        return []

    payload = {'model': EMBED_MODEL, 'input': texts}
    payload_json = json.dumps(payload, ensure_ascii=False).encode('utf-8')

    res = http.post(
        GMS_EMBED_URL,
        headers={
            'Authorization': f'Bearer {GMS_API_KEY}',
            'Content-Type': 'application/json; charset=utf-8',
        },
        data=payload_json,
        timeout=timeout,
    )
    res.raise_for_status()

    data = res.json()['data']
    # 응답 순서가 보장되지만, index로 한 번 더 정렬해 입력 순서와 어긋나지 않게 한다.
    return [item['embedding'] for item in sorted(data, key=lambda d: d['index'])]


def embed_text(text, *, timeout=60):
    """단일 텍스트 임베딩 (대화 → 쿼리 벡터)."""
    return embed_texts([text], timeout=timeout)[0]


def product_embedding_text(product) -> str:
    """제품을 임베딩할 때 쓰는 표준 텍스트. 검색 의미에 기여하는 필드만 모은다."""
    return f"[{product.category}] {product.brand} {product.name}: {product.ai_summary}"
