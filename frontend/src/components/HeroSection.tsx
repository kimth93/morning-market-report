import { PLAYBACK_STEPS } from "../state/playback";

interface Props {
  generatedAt: string;
  sourceNote: string;
  replaying: boolean;
  stepIndex: number;
  onReplay: () => void;
}

function formatGeneratedAt(iso: string): string {
  const date = new Date(iso);
  if (Number.isNaN(date.getTime())) return iso;
  return date.toLocaleString("ko-KR", { timeZone: "Asia/Seoul", dateStyle: "medium", timeStyle: "short" });
}

export default function HeroSection({ generatedAt, sourceNote, replaying, stepIndex, onReplay }: Props) {
  return (
    <section className="py-10">
      <p className="text-sm font-semibold text-primary">Claude 기반 요약 · PoC</p>
      <h1 className="mt-2 text-3xl font-bold text-label-strong">출근 후 5분, 오늘의 시장을 읽으세요</h1>
      <p className="mt-3 text-base text-label-neutral">
        경제·증권 뉴스 Top 5 요약과 당일 시장 전망, 투자포인트 3개를 신뢰도 높게 정리해 드립니다. 모든 요약에는
        출처가 명시됩니다.
      </p>

      <div className="mt-6 flex flex-wrap items-center gap-4">
        <button
          type="button"
          onClick={onReplay}
          disabled={replaying}
          className="rounded-xl bg-primary px-5 py-3 font-semibold text-white hover:bg-primary-hover disabled:cursor-not-allowed disabled:bg-primary-bg-strong"
        >
          {replaying ? "재생 중" : "지금 생성하기"}
        </button>
        <span className="text-sm text-label-alternate">실제 생성이 아니라 저장된 예시 보고서를 다시 보여줍니다</span>
      </div>

      {replaying && (
        <div role="status" className="mt-6 rounded-xl border border-line bg-white p-5 shadow-elev-1">
          <p className="font-semibold text-label-strong">{PLAYBACK_STEPS[stepIndex]}</p>
          <p className="mt-1 text-sm text-label-alternate">저장된 예시 보고서를 불러오고 있습니다.</p>
        </div>
      )}

      <p role="note" className="mt-6 rounded-xl bg-bg-alt px-4 py-3 text-sm text-label-neutral">
        {sourceNote} 생성 시각: {formatGeneratedAt(generatedAt)}
      </p>
    </section>
  );
}
