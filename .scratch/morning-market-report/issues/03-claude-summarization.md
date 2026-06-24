# Claude 요약 + 신뢰성 제어

Status: ready-for-agent

## 부모 이슈

[#2 뉴스 수집 파이프라인](./02-news-collection.md)

## 구축할 내용

Claude API를 통해 각 뉴스를 1-2문단으로 요약합니다. 핵심은 신뢰성 규율 준수:
- 할루시네이션 금지: 원문에 없는 수치·통계 생성 불가
- 단정성 제어: "이 주식을 사세요" 같은 직접 투자 권유 금지, 조건부 표현만 허용
- 편향성 제어: 원뉴스의 톤과 균형 유지

각 요약에 할루시네이션 위험도를 평가 (low/medium/high)합니다.

## 수락 기준

- [ ] Claude API 통합 완료 (anthropic SDK)
- [ ] 뉴스당 1-2문단 요약 생성
- [ ] 프롬프트에서 할루시네이션 금지 명시
- [ ] 요약에 투자 권유 표현 없음 확인
- [ ] 할루시네이션 위험도 평가 (low/medium/high)
- [ ] 요약을 `news_summaries` 테이블에 저장
- [ ] 실제 뉴스 5개로 요약 생성 후 원뉴스와 대조하여 정확성 검증

## 선행 조건

- [#2 뉴스 수집 파이프라인](./02-news-collection.md) 완료 필요

---

## 기술 노트

**신뢰성 규율 프롬프트 원칙:**
```
당신은 금융뉴스 요약 전문가입니다.
- 원문에 있는 정보만 요약하세요 (할루시네이션 금지)
- "반드시", "사세요", "상승한다" 같은 직접 권유는 금지
- "~할 가능성이 있다", "~는 주목할 만하다" 등 조건부 표현만 사용
- 원뉴스의 톤과 균형을 유지하세요
```

**응답 구조:**
```json
{
  "summary": "string (1-2문단)",
  "hallucination_risk": "low|medium|high",
  "contains_investment_directive": false,
  "summary_generated_at": "timestamp"
}
```

**Claude 모델:** claude-3-5-sonnet (또는 최신 프로덕션 모델)
