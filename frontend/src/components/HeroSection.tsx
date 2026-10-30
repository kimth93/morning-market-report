import type { GenerationState } from "../state/generation";
import { GENERATION_STEPS } from "../state/generation";

interface Props {
  state: GenerationState;
  onGenerate: () => void;
  onRetry: () => void;
}

export default function HeroSection({ state, onGenerate, onRetry }: Props) {
  const generating = state.phase === "generating";

  return (
    <section className="py-10">
      <p className="text-sm font-semibold text-primary">Claude 기반 요약</p>
      <h1 className="mt-2 text-3xl font-bold text-label-strong">출근 후 5분, 오늘의 시장을 읽으세요</h1>
      <p className="mt-3 text-base text-label-neutral">
        경제·증권 뉴스 Top 5 요약과 당일 시장 전망, 투자포인트 3개를 신뢰도 높게 정리해 드립니다. 모든 요약에는
        출처가 명시됩니다.
      </p>

      <div className="mt-6 flex flex-wrap items-center gap-4">
        {state.phase === "done" ? (
          <button
            type="button"
            onClick={onGenerate}
            className="rounded-xl bg-primary px-5 py-3 font-semibold text-white hover:bg-primary-hover"
          >
            다시 생성
          </button>
        ) : (
          <button
            type="button"
            onClick={state.phase === "error" ? onRetry : onGenerate}
            disabled={generating}
            className="rounded-xl bg-primary px-5 py-3 font-semibold text-white hover:bg-primary-hover disabled:bg-primary-bg-strong disabled:cursor-not-allowed"
          >
            {state.phase === "error" ? "다시 시도" : "지금 생성하기"}
          </button>
        )}
        <span className="text-sm text-label-alternate">약 1~2분 소요 · 뉴스 5건 요약</span>
      </div>

      {generating && (
        <div role="status" className="mt-6 rounded-xl border border-line bg-white p-5 shadow-elev-1">
          <p className="font-semibold text-label-strong">{GENERATION_STEPS[state.stepIndex]}</p>
          <p className="mt-1 text-sm text-label-alternate">보고서를 생성하고 있습니다. 잠시만 기다려 주세요.</p>
        </div>
      )}

      {state.phase === "error" && (
        <div role="alert" className="mt-6 rounded-xl border border-red-200 bg-red-50 p-5">
          <p className="font-semibold text-red-700">보고서를 생성하지 못했습니다</p>
          <p className="mt-1 text-sm text-red-700">{state.error}</p>
        </div>
      )}

      {state.phase === "done" && (
        <p className="mt-6 text-sm font-semibold text-green-700">오늘의 시장 전망 보고서 생성 완료</p>
      )}
    </section>
  );
}
