# 인수인계 — Beautalk 배포 작업 이어받기

> 다음 Claude 세션이 콜드 스타트로 이어받기 위한 문서. **상태와 다음 할 일만** 담는다 —
> 변경 사항 상세 기록은 [docs/progress.md](progress.md), 배경·이유(포트폴리오용)는
> [docs/deployment.md](deployment.md)에 있다. **먼저 그 둘과 [docs/README.md](README.md)(문서 허브)를 읽어라.**

---

## 0. 한 줄 상황
**Phase 1(코드 배포가능화) + 프론트 API env화 완료.** 지금 **Phase 2(EC2 수동 배포) 진행 중** —
EC2 생성·Docker·DNS·코드+env 배포·DB 마이그레이션/데이터 적재까지 끝났고, **certbot HTTPS 발급부터
이어가면 된다.**

- **작업 브랜치**: `46-deploy-aws-ec2-배포-github-actions-cicd-구축` (develop 최신 + FE 작업 merge 완료)
- **도메인**: `beautalk.site` (GoDaddy 구매, A레코드 연결됨)
- **EC2**: t3.micro, Ubuntu 24.04 LTS, 퍼블릭 IP `52.78.34.135`
  - SSH: `ssh -i <다운로드한 beautalk.pem 경로> ubuntu@52.78.34.135`
  - 코드 위치: `~/beautalk` (배포 브랜치 클론), 컴포즈: `~/beautalk/docker-compose.prod.yml`
  - env 2개 이미 주입됨: `~/beautalk/.env`(compose 변수치환), `~/beautalk/backend/.env`(Django 시크릿)

## 1. ⚠️ 작업 방식 (반드시 지킬 것)
- **git commit/push는 사용자가 직접 한다.** Claude는 **명령만 제공**(실행 금지). 커밋 메시지는 **한 줄**, **Co-Authored-By 트레일러 제외**. (메모리 `git-commit-preferences` 참고)
- **프론트엔드는 별도 팀원 담당.** FE 파일 직접 수정 X → **스펙으로 전달**(충돌 방지). EC2/SSH로 들어가
  실제 배포 명령(Docker·migrate 등)을 실행하는 건 이 작업 한정으로 이미 직접 하고 있음(사용자 동의됨).

## 2. 지금 uncommitted (사용자가 커밋해야 함)
```
 M backend/products_seed.json   # 스테일 픽스처(156건) → 최신(306건, 임베딩·제형 포함) 갱신
```
- 제안 커밋: `git add backend/products_seed.json` → `git commit -m "fix: 제품 시드 픽스처 최신화 (156→306건, 임베딩·제형 포함)"`
- Phase1 변경분은 이미 커밋·푸시됨(`70728c4`). develop·FE 작업(`PR #47~49`)도 이미 merge됨.

## 3. 배포 Phase 상태
### Phase 1 — 코드 배포가능화 (완료) + 프론트 API env화 (완료, PR #49)
상세: progress.md "AWS EC2 배포" 항목. 트러블슈팅(env 변수치환 버그): deployment.md.

### Phase 2 — EC2 수동 배포 (진행 중)
- [x] EC2 생성·Docker·스왑2GB·DNS A레코드·develop merge·env 주입·compose 기동·migrate·loaddata
  (제품 데이터 스테일 발견·수정 포함 — deployment.md "프로덕션 데이터 적재 트러블슈팅")
- [ ] **certbot HTTPS 발급** (nginx.conf에 443 블록 추가 필요) ← 다음 시작점
- [ ] 카카오/구글 콘솔에 배포 redirect URI 등록 (`https://beautalk.site/api/v1/auth/{kakao,google}/callback/`)
- [ ] 프론트 빌드(`VITE_API_BASE=https://beautalk.site/api/v1`) → dist를 EC2 `~/beautalk/frontend/dist`로 전송
- [ ] 수동 E2E 검증: 로그인 → 추천 → 게시판

### Phase 3 — GitHub Actions (미시작) — deployment.md §2

## 4. 다음 할 일 (순서)
1. 위 §2 커밋 (사용자가 실행)
2. DNS 전파 확인 (`nslookup beautalk.site`) → certbot으로 HTTPS 발급 (nginx.conf 443 서버 블록 추가 필요)
3. 카카오/구글 콘솔 redirect URI 등록
4. 프론트 빌드 → dist EC2 전송 → nginx가 정적 서빙
5. 수동 E2E 검증
6. Phase 3: Actions CI(테스트)+CD(SSH 배포)

## 5. 핵심 결정·주의사항
- **gpt-4o 전환 권장** — `.env`에 `GMS_MODEL=gpt-4o` (근거: docs/model-selection-report.md). 추천 24s→8s. (이미 prod env에 적용됨)
- **GMS 크레딧 6/26 소멸** — 배포 앱의 추천·챗봇이 GMS 의존. 새 크레딧 확보 여부 확인 필요.
- **DB는 컨테이너**(RDS 안 씀). **t3.micro 최적화**(스왑+빌드 오프로드+PG튜닝)는 deployment.md §5.
- **OAuth는 HTTPS 필수** — certbot 후 카카오/구글 콘솔에 redirect URI 등록.
- **Seed 픽스처는 데이터가 바뀌면 같이 갱신해야 함** — `backend/products_seed.json` 갱신 과정·교훈은 deployment.md 참고. Phase 3 자동화 전에 이 갱신을 절차화할 것.
- 미해결(저우선): 챗봇 프롬프트 LLM 비결정성(가끔 덜 깔끔), 크롤러 ai_summary 셀렉터 버그(리뷰요약으로 우회 중).

## 6. 이번 프로젝트 현재 상태 (context)
- **하이브리드 추천**(정형 제약 SQL필터+RAG), **챗봇 품질**(그라운딩), **지연**(reasoning_effort), **데이터**(306제품 전제형 충분·요약·임베딩 완비·중복0), **커뮤니티**(제품 다중태그 M2M + 닉네임) 모두 완료. 테스트 63개.
- 남은 큰 덩어리: **배포(이 작업, Phase 2 마무리 + Phase 3)** + 발표. 프론트 연동(하이브리드 필터 UI·게시판 5페이지·닉네임 UI)은 FE 팀원 진행 중.
- 문서 허브: docs/README.md. 배포: docs/deployment.md.
