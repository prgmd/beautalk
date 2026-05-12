# Beautalk 🌿
> 당신의 뷰티 상담사, 뷰토크.

## 프로젝트 소개
화장품 선택에 어려움을 겪는 뷰티 입문자/중급자를 위한 챗봇 기반 개인화 화장품 추천 서비스입니다.
피부타입, 피부 고민, 기피 성분을 입력하면 RAG 파이프라인 기반으로 맞춤 제품을 추천해드립니다.

## 기술 스택
| 구분 | 기술 |
|---|---|
| Backend | Django, DRF |
| Frontend | Vue 3 |
| AI | LangChain, RAG, ChromaDB |
| Infra | AWS, Docker, Nginx |

## 팀원
| 이름 | 역할 | GitHub |
|---|---|---|
| 김채은 | | https://github.com/c7aeun |
| 장준환 | | https://github.com/prgmd |

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