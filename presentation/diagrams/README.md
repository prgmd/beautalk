# 📐 발표용 다이어그램

draw.io(diagrams.net)에서 바로 열어 편집할 수 있는 `.drawio` 파일입니다.

| 파일 | 내용 | 쓰이는 슬라이드 |
|------|------|----------------|
| `01-아키텍처.drawio` | 시스템 아키텍처 (브라우저↔Nginx↔Django↔DB + 외부 API) | 설계/아키텍처 (슬라이드 11) |
| `02-하이브리드-추천-플로우.drawio` | ⭐ 추천 플로우 (대화→SQL필터→완화분기→임베딩정렬→LLM선택→검증→✓/✗) | 설계/RAG (슬라이드 16) |
| `03-인프라.drawio` | 배포 (EC2 1대 + Docker 3컨테이너 + HTTPS + dist 업로드 + CD) | 설계/배포 (슬라이드 18) |

## 여는 법
1. **웹**: <https://app.diagrams.net> → File → Open from → Device → `.drawio` 선택
2. **VS Code**: "Draw.io Integration" 확장 설치 후 파일 더블클릭
3. **PPT로 가져오기**: draw.io에서 File → Export as → **PNG(투명배경, 2x)** 또는 **SVG** → PPT에 삽입

## 색 팔레트 (PPT 톤과 통일)
- 기본 노드: 채움 `#EAF0E4` · 테두리 `#7E8B6D` · 글자 `#33402A` (sage)
- 핵심 단계(SQL·RAG): 채움 `#DCE8D2` · 테두리 `#5E7048` (진녹)
- 외부/완화(주의): 채움 `#F3E7EC` · 테두리 `#B98AA0` (rose)
- DB/인프라: 채움 `#E5EAF2` · 테두리 `#6B7E9E` (blue-gray)
- 결정 분기: 채움 `#FBF3D9` · 테두리 `#C9A227` (gold)

> 추가로 필요하면 만들 수 있는 것: **ERD**, **데이터 파이프라인**(크롤링→AI요약→정제→fixture), **인증/토큰 흐름**, **Git 브랜치 흐름**.
