"""LLM 관측(LangSmith) — 선택적. langsmith 미설치/미설정이면 no-op로 동작한다.

LangChain(프레임워크)은 쓰지 않고, 관측 도구인 LangSmith만 `@traceable`로 얹는다.
핵심 함수(_call_gms·_resolve_constraints·_recommend_candidates)에 데코레이터를 달면
입력·출력·지연이 LangSmith 대시보드로 흘러, 프롬프트가 왜 그렇게 답하는지 눈으로 본다.

활성화:
  1) pip install langsmith
  2) .env 에
       LANGSMITH_TRACING=true
       LANGSMITH_API_KEY=ls__...
       LANGSMITH_PROJECT=beautalk      # 선택
미설정이면 데코레이터는 원함수를 그대로 돌려주는 no-op이라 운영/테스트에 영향 없다.
"""

try:
    from langsmith import traceable  # noqa: F401  (설치 시 실제 추적 데코레이터)
except ImportError:
    def traceable(*d_args, **d_kwargs):
        """langsmith 미설치 시 no-op. @traceable / @traceable(name=..) 둘 다 지원."""
        # @traceable (괄호 없이) — 첫 인자가 곧 데코레이트 대상 함수.
        if len(d_args) == 1 and callable(d_args[0]) and not d_kwargs:
            return d_args[0]

        # @traceable(name=..) (팩토리) — 데코레이터를 돌려준다.
        def decorator(fn):
            return fn
        return decorator
