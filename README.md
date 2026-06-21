# Beautalk 🌿
> 당신의 뷰티 상담사, 뷰토크.

## 프로젝트 소개
화장품 선택에 어려움을 겪는 뷰티 입문자를 위한 챗봇 기반 개인화 화장품 추천 서비스로, 피부타입, 피부 고민, 기피 성분을 입력하면 AI 상담사가 맞춤 제품을 추천해드립니다. 어렵지 않습니다. 당신의 뷰티를 책임질 친구, '뷰토크'와 이야기를 하다보면 어느 순간 자연스레 자신에게 맞춤 제품을 찾을 수 있을 것입니다.

## 기술 스택
| 구분 | 기술 |
|---|---|
| Backend | Django |
| Frontend | Vue 3 |
| AI | LLM |
| Infra | AWS, Docker, Nginx |

- REST API 구축: DRF
- JWT 구현: simplejwt

## 문서

| 파일 | 설명 |
|---|---|
| [docs/API.md](docs/API.md) | API 명세서 (엔드포인트, Request/Response, 에러 코드) |
| [docs/progress.md](docs/progress.md) | 구현 현황 및 진행 예정 작업 |
| [docs/structure.md](docs/structure.md) | 프로젝트 디렉토리 구조 |
| [docs/plan.md](docs/plan.md) | 보안 취약점 진단·해결, RAG 도입 계획, 잔여 작업 로드맵 |

## 팀원
| 이름 | 역할 | GitHub |
|---|---|---|
| 김채은 | 프론트엔드 | https://github.com/c7aeun |
| 장준환 | 백엔드 | https://github.com/prgmd |

## 시작하기

### 요구사항
- Python 3.11+
- Node.js 20+
- Docker

### 실행
```bash
# 레포 클론
git clone https://github.com/[org]/beautalk.git
cd beautalk

# 백엔드
cd backend
pip install -r requirements.txt
python manage.py migrate
python manage.py runserver

# 프론트엔드
cd frontend
npm install
npm run dev

# Docker로 실행
docker-compose up --build
```