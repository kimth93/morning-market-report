interface Props {
  generatedAt: string;
  sourceNote: string;
}

function formatGeneratedAt(iso: string): string {
  const date = new Date(iso);
  if (Number.isNaN(date.getTime())) return iso;
  return date.toLocaleString("ko-KR", { timeZone: "Asia/Seoul", dateStyle: "medium", timeStyle: "short" });
}

export default function HeroSection({ generatedAt, sourceNote }: Props) {
  return (
    <section className="py-10">
      <p className="text-sm font-semibold text-primary">Claude 기반 요약 · 포트폴리오 PoC</p>
      <h1 className="mt-2 text-3xl font-bold text-label-strong">출근 후 5분, 오늘의 시장을 읽으세요</h1>
      <p className="mt-3 text-base text-label-neutral">
        경제·증권 뉴스 Top 5 요약과 당일 시장 전망, 투자포인트 3개를 신뢰도 높게 정리해 드립니다. 모든 요약에는
        출처가 명시됩니다.
      </p>
      <p role="note" className="mt-6 rounded-xl bg-bg-alt px-4 py-3 text-sm text-label-neutral">
        {sourceNote} 생성 시각: {formatGeneratedAt(generatedAt)}
      </p>
    </section>
  );
}
