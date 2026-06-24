# 인수인계 — Beautalk 배포 작업 이어받기

> 다음 Claude 세션이 콜드 스타트로 이어받기 위한 문서. **상태와 다음 할 일만** 담는다 —
> 변경 사항 상세 기록은 [docs/progress.md](progress.md), 배경·이유(포트폴리오용)는
> [docs/deployment.md](deployment.md)에 있다. **먼저 그 둘과 [docs/README.md](README.md)(문서 허브)를 읽어라.**

---

## 0. 한 줄 상황
백엔드 기능·데이터 정제 **완료**. **AWS EC2 배포 Phase 1 완료** (코드 배포가능화 + 회귀테스트 +
로컬 prod compose 검증). 남은 건 **프론트 API env화(FE 팀원) + Phase 2(EC2 수동) + Phase 3(Actions)**.

- **작업 브랜치**: `46-deploy-aws-ec2-배포-github-actions-cicd-구축`
- **도메인**: `beautalk.site` (구매됨), **EC2**: t3.micro (프리티어 소진)

## 1. ⚠️ 작업 방식 (반드시 지킬 것)
- **git commit/push는 사용자가 직접 한다.** Claude는 **명령만 제공**(실행 금지). 커밋 메시지는 **한 줄**, **Co-Authored-By 트레일러 제외**. (메모리 `git-commit-preferences` 참고)
- **프론트엔드는 별도 팀원 담당.** FE 파일 직접 수정 X → **스펙으로 전달**(충돌 방지).

## 2. 지금 uncommitted (사용자가 커밋해야 함)
브랜치 `46`에서 Phase 1 전체 변경분 (무엇을·왜 변경했는지는 progress.md/deployment.md 참고):
```
 M backend/accounts/views.py  M backend/config/settings.py  M backend/requirements.txt
 M docs/README.md  M docs/progress.md  M .gitignore
?? backend/Dockerfile  ?? backend/.env.prod.example
?? docker-compose.prod.yml  ?? nginx/  ?? .env.prod.example
?? docs/deployment.md  ?? docs/HANDOFF.md
```
- 제안 커밋(한 줄, 사용자 실행):
  `git add backend/ nginx/ docker-compose.prod.yml docs/ .gitignore .env.prod.example`
  `git commit -m "feat: 배포 Phase1 — 코드 배포가능화 (env화·Dockerfile·nginx·compose.prod) + 로컬검증"`

> 참고: 직전 develop 작업분(dedupe_products M2M 수정, 챗봇 스킨↔토너 프롬프트 수정)은 현재 uncommitted에 없음 → 이미 커밋된 것으로 보임. `git log`로 확인.

## 3. 배포 Phase 상태
### Phase 1 — 코드 배포가능화 (완료)
모든 항목 완료 (회귀 테스트·로컬 prod compose 검증 포함). 상세: progress.md "AWS EC2 배포" 항목,
검증 중 발견한 버그 분석은 deployment.md "로컬 검증 트러블슈팅".
- [ ] **프론트 API base env화 (FE 팀원)** — 스펙은 deployment.md "프론트엔드 변경 spec"
### Phase 2 — EC2 수동 배포 (미시작) — deployment.md §2
### Phase 3 — GitHub Actions (미시작) — deployment.md §2

## 4. 다음 할 일 (순서)
1. 위 §2 커밋 (사용자가 실행)
2. 프론트 API env화 (FE 팀원에게 스펙 전달)
3. Phase 2: EC2 생성(보안그룹 22/80/443) → Docker설치 → 스왑2GB(deployment.md §5) → 도메인 A레코드 →
   **env 2개 주입**(루트 `.env` + `backend/.env`, `DB_*` 값 동일하게 — deployment.md 트러블슈팅 참고) →
   `docker compose -f docker-compose.prod.yml up -d --build` → migrate/loaddata/backfill →
   **certbot HTTPS**(nginx.conf에 443 블록 추가) → 카카오/구글 콘솔에 배포 redirect URI 등록 → E2E 검증
4. Phase 3: Actions CI(테스트)+CD(SSH 배포)

## 5. 핵심 결정·주의사항
- **gpt-4o 전환 권장** — `.env`에 `GMS_MODEL=gpt-4o` (근거: docs/model-selection-report.md). 추천 24s→8s.
- **GMS 크레딧 6/26 소멸** — 배포 앱의 추천·챗봇이 GMS 의존. 새 크레딧 확보 여부 확인 필요.
- **DB는 컨테이너**(RDS 안 씀). **t3.micro 최적화**(스왑+빌드 오프로드+PG튜닝)는 deployment.md §5.
- **OAuth는 HTTPS 필수** — Phase 2에서 certbot 후 카카오/구글 콘솔에 `https://beautalk.site/api/v1/auth/{kakao,google}/callback/` 등록.
- 미해결(저우선): 챗봇 프롬프트 LLM 비결정성(가끔 덜 깔끔), 크롤러 ai_summary 셀렉터 버그(리뷰요약으로 우회 중).

## 6. 이번 프로젝트 현재 상태 (context)
- **하이브리드 추천**(정형 제약 SQL필터+RAG), **챗봇 품질**(그라운딩), **지연**(reasoning_effort), **데이터**(306제품 전제형 충분·요약·임베딩 완비·중복0), **커뮤니티**(제품 다중태그 M2M + 닉네임) 모두 완료. 테스트 63개.
- 남은 큰 덩어리: **배포(이 작업)** + **프론트 연동**(FE 팀원: 하이브리드 필터 UI·게시판 5페이지·닉네임 UI) + 발표.
- 문서 허브: docs/README.md. 배포: docs/deployment.md.
