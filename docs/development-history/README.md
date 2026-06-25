> 개발 이력 문서 · beautalk

# 개발 이력 (Development History)

beautalk을 **어떤 순서로, 무엇을, 왜 그렇게** 만들었는지를 일반적인 개발 프로세스(기획 → 설계 → 환경 → 데이터 → 기능 → 배포 → 검증)에 맞춰 정리한 문서 모음입니다.
각 문서는 **비전공자도 읽을 수 있게** 쉬운 말로 썼고, "어떤 선택지가 있었고 무엇을 왜 골랐는지"를 함께 적었습니다.

> 더 깊은 기술 기록(설계 원본·트러블슈팅 원문)은 상위 [docs 폴더](../README.md)에 있습니다. 이 폴더는 그것들을 **하나의 이야기로 다시 엮은 요약본**입니다.

---

## 읽는 순서

| # | 문서 | 한 줄 요약 |
|---|------|-----------|
| 01 | [기획](01-planning.md) | "화장품 고르기 막막함"을 대화형 추천으로 풀기로 정하고, 꼭 할 것/포기할 것을 가렸다 |
| 02 | [설계](02-design.md) | 시스템 구조·데이터 설계도(ERD)·API 약속(RESTful)을 그리고, 왜 Django REST + Vue SPA인지 정했다 |
| 03 | [협업 환경 — Git 전략](03-collaboration.md) | 여러 명이 충돌 없이 함께 짜도록 `develop`+기능 브랜치+PR 전략을 세웠다 |
| 04 | [데이터 확보와 정제](04-data.md) | 올리브영 제품을 크롤링해 모으고, 리뷰를 AI로 요약하고, 깨끗이 정제해 재현 가능한 fixture로 만들었다 |
| 05 | [인증과 보안](05-auth-security.md) | 소셜 로그인(OAuth)+JWT 출입증, 소유권 검사(IDOR 방어), 시크릿 0건 커밋으로 안전하게 만들었다 |
| 06 | [챗봇 — 대화와 추천 분리](06-chatbot-recommendation.md) | 챗봇을 '대화로 정보 모으기'와 '추천 만들기' 두 단계로 나눠 LLM의 혼란을 줄였다 |
| 07 | [RAG와 하이브리드 추천](07-rag-hybrid-recommendation.md) | **(핵심)** "로션 요청에 크림" 오추천을, SQL 필터(하드 조건)+AI 검색(소프트 취향) 2겹으로 박멸했다 |
| 08 | [커뮤니티 게시판](08-community.md) | 용도별 게시판 + 제품 태그로, 추천받은 제품과 사용 후기를 글로 잇는 소통 공간을 만들었다 |
| 09 | [프론트엔드와 디자인](09-frontend-design.md) | Vue SPA를 부품·상태·라우팅으로 짜고, 디자인 토큰으로 모바일 우선의 통일감 있는 UI를 완성했다 |
| 10 | [배포](10-deployment.md) | "내 컴퓨터에서만 되던 것"을 AWS 서버 한 대에 Docker로 올려 `beautalk.site`로 누구나 접속하게 했다 |
| 11 | [테스트와 트러블슈팅](11-testing-troubleshooting.md) | 자동화 테스트 63개로 안전망을 깔고, 실제로 겪은 8개 문제를 증상→원인→해결로 정리했다 |

---

## 한 장으로 보는 흐름

```
[01 기획] 문제 정의·기능 우선순위
    │
[02 설계] 아키텍처 · ERD · REST API
    │
[03 협업] Git 전략으로 병렬 개발 기반 마련
    │
[04 데이터] 크롤링 → AI 요약 → 정제 → fixture   ← "양질의 데이터가 추천의 토대"
    │
[05 인증·보안] OAuth 로그인 · JWT · 권한 · 시크릿 분리
    │
[06 챗봇]  대화 단계 ↔ 추천 단계 분리
    │
[07 추천]  SQL 필터(하드) + RAG 임베딩(소프트) = 하이브리드   ← 프로젝트 핵심
    │
[08 커뮤니티] 용도별 게시판 + 제품 태그(정참조·역참조)
    │
[09 프론트] Vue SPA · 라우터 가드 · 디자인 시스템
    │
[10 배포]  EC2 + Docker(db·backend·nginx) + HTTPS → beautalk.site
    │
[11 검증]  자동 테스트 63개 · 트러블슈팅 · 회고
```

---

## 명세서 요구사항과의 연결 (요약)

| 명세서 항목 | 다룬 문서 |
|---|---|
| F1301 사용자 추천 | [06](06-chatbot-recommendation.md) · [07](07-rag-hybrid-recommendation.md) |
| F1302 API 활용 (LLM 등) | [04](04-data.md) · [06](06-chatbot-recommendation.md) |
| F1303 커뮤니티 | [08](08-community.md) |
| F1304 RESTful 설계 | [02](02-design.md) · [11](11-testing-troubleshooting.md) |
| F1305 서비스 배포 (심화) | [10](10-deployment.md) |
| NF1301 Git 활용 | [03](03-collaboration.md) |
| NF1302 API Key 관리 | [05](05-auth-security.md) |
| NF1303 데이터 확보 | [04](04-data.md) |
| NF1304 페이지 다양성 | [08](08-community.md) · [09](09-frontend-design.md) |

> 항목별 "어떻게 충족했는지"의 자세한 근거는 [요구사항 충족 정리](../requirements-compliance.md)를 보세요.
