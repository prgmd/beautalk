# 인수인계 — Beautalk 배포 작업 이어받기

> 다음 Claude 세션이 콜드 스타트로 이어받기 위한 문서. **상태와 다음 할 일만** 담는다 —
> 변경 사항 상세 기록은 [docs/progress.md](progress.md), 배경·이유(포트폴리오용)는
> [docs/deployment.md](deployment.md)에 있다. **먼저 그 둘과 [docs/README.md](README.md)(문서 허브)를 읽어라.**

---

## 0. 한 줄 상황
**배포 Phase 1·2·3 전부 완료 — `https://beautalk.site` 운영 중 + develop push 시 자동 배포(CI/CD) 동작.**
로그인(카카오·구글)·온보딩·챗봇·추천·찜·커뮤니티까지 수동 E2E 전 구간 통과. **배포 작업은 사실상 끝.**
남은 건 발표 준비, 그리고 FE 팀원의 화면 연동.

- **작업 브랜치**: **`develop`에서 직접 작업**(Phase1·2는 PR #53으로 merge 완료). develop push = 자동 배포
- **도메인**: `beautalk.site` (HTTPS, Let's Encrypt 인증서 만료 2026-09-22)
- **EC2**: t3.micro, Ubuntu 24.04 LTS, 퍼블릭 IP `52.78.34.135`
  - SSH: `ssh -i <다운로드한 beautalk.pem 경로> ubuntu@52.78.34.135`
  - 코드 위치: `~/beautalk` (**이제 develop 브랜치** 추적), 컴포즈: `~/beautalk/docker-compose.prod.yml`
  - env 2개 이미 주입됨: `~/beautalk/.env`(compose 변수치환), `~/beautalk/backend/.env`(Django 시크릿)
  - certbot 인증서: `~/beautalk/certbot/`(루트 소유, gitignore)

## 1. ⚠️ 작업 방식 (반드시 지킬 것)
- **git commit/push는 사용자가 직접 한다.** Claude는 **명령만 제공**(실행 금지). 커밋 메시지는 **한 줄**, **Co-Authored-By 트레일러 제외**. (메모리 `git-commit-preferences` 참고)
- **프론트엔드는 별도 팀원 담당.** FE 파일 직접 수정 X → **스펙으로 전달**(충돌 방지). EC2/SSH로 들어가
  실제 배포 명령(Docker·migrate 등)을 실행하는 건 이 작업 한정으로 직접 하고 있음(사용자 동의됨).

## 2. 배포 Phase 상태
- **Phase 1** — 코드 배포가능화 + 프론트 API env화: **완료**
- **Phase 2** — EC2 수동 배포: **완료** (EC2·Docker·DNS·certbot HTTPS·OAuth redirect·프론트
  dist·E2E 검증 전부 끝). 트러블슈팅 기록: deployment.md (스테일 시드 픽스처, 카카오 `KOE006`
  redirect_uri 오타, Docker baked-in 이미지 vs 호스트 마운트 등)
- **Phase 3** — GitHub Actions CI/CD: **완료** — `.github/workflows/ci-cd.yml`(`test` → `deploy`).
  develop push → test 통과 → 프론트 빌드 → EC2 자동 배포(`reset --hard` + dist 교체 + compose +
  migrate) → 검증까지 동작 확인. Secrets 등록·EC2 develop 전환 완료.
  - 트러블슈팅 2건(상세: deployment.md "Actions CD 트러블슈팅"):
    ① 보안그룹 SSH 22가 "내 IP"로만 열려 Actions 러너 차단 → `0.0.0.0/0` 개방
    ② CD가 `rm -rf dist`로 inode를 바꿔 nginx 바인드 마운트가 빈 디렉터리 가리킴(403) →
       `find -delete`로 내용만 비워 inode 보존하도록 수정
  - ⚠️ **운영 주의**: CD가 EC2에서 `git reset --hard origin/develop`을 돌리므로 **서버에서 직접
    고친 추적 파일은 매 배포 때 버려진다** — 변경은 반드시 develop에 반영할 것. (.env·certbot·dist는
    gitignore라 안전.) **보안그룹 SSH 22가 전세계 개방** 상태(키 인증 전용이라 수용 가능하나 인지할 것).

## 3. 핵심 결정·주의사항
- **gpt-4o 적용됨** — prod env `GMS_MODEL=gpt-4o` (근거: docs/model-selection-report.md).
- **GMS 크레딧 6/26 소멸** — 추천·챗봇이 GMS 의존. 새 크레딧 확보 여부 확인 필요.
- **DB는 컨테이너**(RDS 안 씀). **Seed 픽스처는 데이터가 바뀌면 같이 갱신해야 함**(deployment.md
  "프로덕션 데이터 적재 트러블슈팅") — Phase 3 자동화 전에 절차화할 것.
- **시드 픽스처는 데이터 바뀌면 같이 갱신**(`backend/products_seed.json`) — CD가 loaddata를
  자동화하진 않으므로, 데이터 변동 시 픽스처 갱신 후 EC2에서 수동 재적재 필요(deployment.md 참고).
- 미해결(저우선): 챗봇 프롬프트 LLM 비결정성(가끔 덜 깔끔), 크롤러 ai_summary 셀렉터 버그(리뷰요약으로 우회 중).

## 4. 이번 프로젝트 현재 상태 (context)
- **하이브리드 추천**(정형 제약 SQL필터+RAG), **챗봇 품질**(그라운딩), **데이터**(306제품·임베딩·중복0),
  **커뮤니티**(제품 다중태그 M2M + 닉네임), **배포**(Phase1·2·3, CI/CD 자동화) 모두 완료. 테스트 63개.
- 남은 큰 덩어리: **발표 준비** + 프론트 연동(하이브리드 필터 UI·게시판 5페이지, FE 팀원 진행 중).
- 문서 허브: docs/README.md. 배포: docs/deployment.md.
