// 공개 PoC의 "지금 생성"은 실제 생성이 아니라 저장된 예시 보고서를 재생하는 것이다.
// 외부 API를 호출하지 않으므로 비용이 생기지 않는다.
export const PLAYBACK_STEPS = [
  "뉴스를 수집하고 있습니다",
  "기사를 요약하고 있습니다",
  "시장 전망을 작성하고 있습니다",
];

export function nextStepIndex(current: number): number {
  return (current + 1) % PLAYBACK_STEPS.length;
}
