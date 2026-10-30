import { useState, type FormEvent } from "react";
import type { GenerateResponse } from "../api/news";
import { signupSubscriber } from "../api/subscription";

interface Props {
  result?: GenerateResponse;
}

type Status =
  | { kind: "idle" }
  | { kind: "submitting" }
  | { kind: "success"; subscriptionId: string }
  | { kind: "error"; message: string };

export default function EmailSubscription({ result }: Props) {
  const [name, setName] = useState("");
  const [email, setEmail] = useState("");
  const [status, setStatus] = useState<Status>({ kind: "idle" });

  const handleSubmit = async (e: FormEvent<HTMLFormElement>) => {
    e.preventDefault();
    setStatus({ kind: "submitting" });
    try {
      const response = await signupSubscriber({ email, name });
      setStatus({ kind: "success", subscriptionId: response.subscription_id });
    } catch (error) {
      setStatus({ kind: "error", message: error instanceof Error ? error.message : "알 수 없는 오류가 발생했습니다" });
    }
  };

  return (
    <section className="pb-10">
      <div className="rounded-2xl border border-line bg-white p-6 shadow-elev-1">
        <h2 className="text-xl font-bold text-label-strong">매일 아침 자동 발송 이메일로 받아보기</h2>
        <p className="mt-1 text-sm text-label-neutral">
          구독하시면 매일 아침 이 보고서를 메일함에서 바로 확인하실 수 있습니다.
        </p>

        <form onSubmit={handleSubmit} className="mt-4 flex flex-col gap-3 sm:flex-row">
          <input
            type="text"
            required
            value={name}
            onChange={(e) => setName(e.target.value)}
            placeholder="이름"
            aria-label="이름"
            className="rounded-xl border border-line-strong px-4 py-3"
          />
          <input
            type="email"
            required
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            placeholder="이메일 주소"
            aria-label="이메일 주소"
            className="flex-1 rounded-xl border border-line-strong px-4 py-3"
          />
          <button
            type="submit"
            disabled={status.kind === "submitting"}
            className="rounded-xl bg-primary px-5 py-3 font-semibold text-white hover:bg-primary-hover disabled:cursor-not-allowed disabled:bg-primary-bg-strong"
          >
            {status.kind === "submitting" ? "신청 중" : "구독 신청하기"}
          </button>
        </form>

        {status.kind === "success" && (
          <p role="status" className="mt-3 text-sm font-semibold text-green-700">
            구독 신청이 완료되었습니다 (구독 ID: {status.subscriptionId}). 실제 발송은 v2에서 제공됩니다.
          </p>
        )}
        {status.kind === "error" && (
          <p role="alert" className="mt-3 text-sm text-red-700">
            {status.message}
          </p>
        )}
        <p className="mt-2 text-xs text-label-assistive">
          구독 신청 시 서비스 안내 목적의 메일 수신에 동의하는 것으로 간주됩니다.
        </p>

        <div className="mt-6 rounded-xl bg-bg-alt p-4 text-sm text-label-neutral">
          <p className="text-xs font-semibold text-label-alternate">받게 될 이메일 미리보기</p>
          {result ? <EmailPreview result={result} /> : (
            <p className="mt-2">
              '지금 생성하기'로 보고서를 만들면, 같은 내용이 이메일 형태로 여기에 표시됩니다.
            </p>
          )}
          <p className="mt-3 text-xs text-label-alternate">
            투자 참고용이며 투자 권유가 아닙니다. 최종 판단과 책임은 본인에게 있습니다.
          </p>
        </div>
      </div>
    </section>
  );
}

function EmailPreview({ result }: { result: GenerateResponse }) {
  return (
    <div className="mt-2 space-y-3">
      <p className="font-semibold text-label-strong">[아침 시장 전망] 오늘의 시장 브리핑</p>
      <div>
        <p className="font-semibold text-label-strong">오늘의 시장 전망</p>
        <p className="mt-1">{result.market_outlook}</p>
      </div>
      <div>
        <p className="font-semibold text-label-strong">주목할 투자포인트</p>
        <ul className="mt-1 list-disc space-y-1 pl-5">
          {result.investment_points.filter(Boolean).slice(0, 3).map((point, index) => (
            <li key={index}>{point}</li>
          ))}
        </ul>
      </div>
      <div>
        <p className="font-semibold text-label-strong">뉴스 Top 5</p>
        <ol className="mt-1 list-decimal space-y-2 pl-5">
          {result.news_items.map((item) => (
            <li key={item.url}>
              <span className="font-semibold text-label-strong">{item.title}</span>
              <span className="block text-label-alternate">{item.summary}</span>
            </li>
          ))}
        </ol>
      </div>
    </div>
  );
}
