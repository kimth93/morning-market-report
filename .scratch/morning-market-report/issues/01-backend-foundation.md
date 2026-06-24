# 백엔드 기초 & 데이터베이스 설정

Status: ready-for-agent

## 구축할 내용

FastAPI 기반 백엔드 서버를 초기화하고, 뉴스 데이터를 저장할 SQLite 데이터베이스 스키마를 설계합니다. 환경 변수 관리와 기본 API 엔드포인트를 구성하여 모든 후속 기능의 기반을 마련합니다.

## 수락 기준

- [ ] FastAPI 서버가 정상 실행되고 기본 헬스 체크 엔드포인트 (`GET /health`) 응답
- [ ] SQLite 데이터베이스 스키마 설계 및 생성 (뉴스, 요약, 구독자 테이블)
- [ ] 환경 변수 설정 (`.env` 파일 및 `python-dotenv` 로드)
- [ ] Claude API 키, Naver News API 키 설정 가능
- [ ] 기본 폴더 구조 설정 (backend/, frontend/, 등)

## 선행 조건

None - 즉시 시작 가능

---

## 기술 노트

**데이터베이스 스키마:**
```
news_items:
  - id (PK)
  - title
  - source
  - date
  - url
  - collected_at

news_summaries:
  - id (PK)
  - news_id (FK)
  - summary_text
  - hallucination_risk (low|medium|high)
  - generated_at

email_subscribers:
  - id (PK)
  - email
  - name
  - subscribed_at
```

**필수 라이브러리:**
- fastapi
- uvicorn
- anthropic
- requests
- sqlalchemy
- python-dotenv
