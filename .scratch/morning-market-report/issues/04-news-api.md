# 뉴스 요약 API 및 저장

Status: ready-for-agent

## 부모 이슈

[#1 백엔드 기초 & 데이터베이스 설정](./01-backend-foundation.md)  
[#3 Claude 요약 + 신뢰성 제어](./03-claude-summarization.md)

## 구축할 내용

뉴스 수집 → 요약 생성 → 저장의 전체 파이프라인을 하나의 API 엔드포인트로 통합합니다. 프론트엔드의 "지금 생성" 버튼이 호출할 `POST /api/news/generate` 엔드포인트를 구현하고, 구조화된 JSON 응답을 반환합니다.

## 수락 기준

- [ ] `POST /api/news/generate` 엔드포인트 구현
- [ ] 호출 시 뉴스 5개 수집 → Claude로 요약 → 결과 저장
- [ ] 응답에 다음 포함: 뉴스 제목, 언론사, 발행일, URL, 요약, 할루시네이션 위험도
- [ ] 응답 시간 < 5분 (또는 프론트엔드에서 진행바 표시 가능하도록)
- [ ] 실제 뉴스 5개로 엔드투엔드 테스트
- [ ] 응답 데이터가 명세와 정확히 일치

## 선행 조건

- [#1 백엔드 기초 & 데이터베이스 설정](./01-backend-foundation.md) 완료
- [#3 Claude 요약 + 신뢰성 제어](./03-claude-summarization.md) 완료

---

## 기술 노트

**API 응답 스키마:**
```json
{
  "news_items": [
    {
      "title": "string",
      "source": "string",
      "date": "2026-06-24",
      "url": "string",
      "summary": "string (1-2문단)",
      "hallucination_risk": "low|medium|high"
    }
  ],
  "generated_at": "2026-06-24T10:30:00Z"
}
```

**비용 추적:**
- API 호출 비용 로깅 (Claude API 토큰 사용량)
- 일일/월별 비용 집계 가능하도록 구현
