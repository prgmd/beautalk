# 인수인계 — Beautalk 배포 작업 이어받기

> 다음 Claude 세션이 콜드 스타트로 이어받기 위한 문서. **상태와 다음 할 일만** 담는다 —
> 변경 사항 상세 기록은 [docs/progress.md](progress.md), 배경·이유(포트폴리오용)는
> [docs/deployment.md](deployment.md)에 있다. **먼저 그 둘과 [docs/README.md](README.md)(문서 허브)를 읽어라.**

---

## 0. 한 줄 상황
**Phase 1·2 완료 — `https://beautalk.site` 실제로 운영 중.** 로그인(카카오·구글)·온보딩·챗봇·추천·
찜·커뮤니티 게시판까지 수동 E2E 전 구간 통과. 지금 **Phase 3(GitHub Actions CI/CD) 착수.**

- **작업 브랜치**: `46-deploy-aws-ec2-배포-github-actions-cicd-구축` (develop 최신 + FE 작업 merge 완료)
- **도메인**: `beautalk.site` (HTTPS, Let's Encrypt 인증서 만료 2026-09-22)
- **EC2**: t3.micro, Ubuntu 24.04 LTS, 퍼블릭 IP `52.78.34.135`
  - SSH: `ssh -i <다운로드한 beautalk.pem 경로> ubuntu@52.78.34.135`
  - 코드 위치: `~/beautalk` (배포 브랜치 클론), 컴포즈: `~/beautalk/docker-compose.prod.yml`
  - env 2개 이미 주입됨: `~/beautalk/.env`(compose 변수치환), `~/beautalk/backend/.env`(Django 시크릿)

## 1. ⚠️ 작업 방식 (반드시 지킬 것)
- **git commit/push는 사용자가 직접 한다.** Claude는 **명령만 제공**(실행 금지). 커밋 메시지는 **한 줄**, **Co-Authored-By 트레일러 제외**. (메모리 `git-commit-preferences` 참고)
- **프론트엔드는 별도 팀원 담당.** FE 파일 직접 수정 X → **스펙으로 전달**(충돌 방지). EC2/SSH로 들어가
  실제 배포 명령(Docker·migrate 등)을 실행하는 건 이 작업 한정으로 직접 하고 있음(사용자 동의됨).

## 2. 배포 Phase 상태
- **Phase 1** — 코드 배포가능화 + 프론트 API env화: **완료**
- **Phase 2** — EC2 수동 배포: **완료** (EC2·Docker·DNS·certbot HTTPS·OAuth redirect·프론트
  dist·E2E 검증 전부 끝). 트러블슈팅 기록: deployment.md (스테일 시드 픽스처, 카카오 `KOE006`
  redirect_uri 오타, Docker baked-in 이미지 vs 호스트 마운트 등)
- **Phase 3** — GitHub Actions CI/CD: **착수** — deployment.md §2 참고
  - [ ] CI: PR/push에 Django 테스트(PG service 컨테이너)
  - [ ] CD: 배포 브랜치 push → SSH로 EC2 접속 → `git pull` + `docker compose up -d --build` + `migrate`
  - [ ] Secrets: `EC2_HOST`, `EC2_SSH_KEY`, `EC2_USER` 등 GitHub repo secrets 등록 필요
  - [ ] **미결정**: 배포 트리거 브랜치 — `main`(신규, 배포 전용) vs `develop` 그대로 (deployment.md §4)

## 3. 핵심 결정·주의사항
- **gpt-4o 적용됨** — prod env `GMS_MODEL=gpt-4o` (근거: docs/model-selection-report.md).
- **GMS 크레딧 6/26 소멸** — 추천·챗봇이 GMS 의존. 새 크레딧 확보 여부 확인 필요.
- **DB는 컨테이너**(RDS 안 씀). **Seed 픽스처는 데이터가 바뀌면 같이 갱신해야 함**(deployment.md
  "프로덕션 데이터 적재 트러블슈팅") — Phase 3 자동화 전에 절차화할 것.
- 미해결(저우선): 챗봇 프롬프트 LLM 비결정성(가끔 덜 깔끔), 크롤러 ai_summary 셀렉터 버그(리뷰요약으로 우회 중).

## 4. 이번 프로젝트 현재 상태 (context)
- **하이브리드 추천**(정형 제약 SQL필터+RAG), **챗봇 품질**(그라운딩), **데이터**(306제품·임베딩·중복0),
  **커뮤니티**(제품 다중태그 M2M + 닉네임), **배포**(Phase1·2) 모두 완료. 테스트 63개.
- 남은 큰 덩어리: **Phase 3(Actions)** + 프론트 연동(하이브리드 필터 UI·게시판 5페이지, FE 팀원 진행 중) + 발표.
- 문서 허브: docs/README.md. 배포: docs/deployment.md.
