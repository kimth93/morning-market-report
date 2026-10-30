import type { GenerateResponse } from "../api/news";
import { formatDate, safeHttpUrl } from "../lib/format";
import RiskBadge from "./RiskBadge";

export default function ResultsSection({ result }: { result: GenerateResponse }) {
  const points = result.investment_points.filter(Boolean).slice(0, 3);

  return (
    <section className="space-y-8 pb-10">
      <div className="rounded-2xl border border-line bg-white p-6 shadow-elev-1">
        <p className="text-xs font-semibold tracking-wide text-primary">MARKET OUTLOOK</p>
        <h2 className="mt-1 text-xl font-bold text-label-strong">오늘의 시장 전망</h2>
        <p className="mt-3 leading-relaxed text-label">{result.market_outlook}</p>
      </div>

      <div className="rounded-2xl border border-line bg-white p-6 shadow-elev-1">
        <h2 className="text-xl font-bold text-label-strong">주목할 투자포인트</h2>
        <ol className="mt-4 space-y-3">
          {points.map((point, index) => (
            <li key={index} className="flex gap-3">
              <span className="flex h-6 w-6 flex-shrink-0 items-center justify-center rounded-full bg-primary-bg text-sm font-bold text-primary">
                {index + 1}
              </span>
              <span className="text-label">{point}</span>
            </li>
          ))}
        </ol>
      </div>

      <div>
        <h2 className="text-xl font-bold text-label-strong">경제·증권 뉴스 Top 5</h2>
        <p className="mt-1 text-sm text-label-alternate">출처 명시 · 원문 링크 제공</p>
        <ul className="mt-4 space-y-4">
          {result.news_items.map((item) => {
            const link = safeHttpUrl(item.url);
            return (
              <li key={item.url} className="rounded-2xl border border-line bg-white p-5 shadow-elev-1">
                <div className="flex flex-wrap items-start justify-between gap-3">
                  <h3 className="text-base font-semibold text-label-strong">{item.title}</h3>
                  <RiskBadge level={item.hallucination_risk} />
                </div>
                <p className="mt-3 leading-relaxed text-label-neutral">{item.summary}</p>
                <div className="mt-4 flex flex-wrap items-center gap-x-3 gap-y-1 text-sm text-label-alternate">
                  <span>{item.source}</span>
                  <span aria-hidden="true">·</span>
                  <span>{formatDate(item.date)}</span>
                  {link && (
                    <>
                      <span aria-hidden="true">·</span>
                      <a
                        href={link}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="font-semibold text-primary hover:text-primary-hover"
                      >
                        원문 보기
                      </a>
                    </>
                  )}
                </div>
              </li>
            );
          })}
        </ul>
        <p className="mt-6 text-sm text-label-alternate">
          본 보고서는 투자 참고용 정보이며, 투자 권유가 아닙니다. 투자에 대한 최종 판단과 책임은 본인에게 있습니다.
        </p>
      </div>
    </section>
  );
}
