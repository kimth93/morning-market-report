import { useState, type FormEvent } from "react";

export default function EmailSubscription() {
  const [email, setEmail] = useState("");
  const [submitted, setSubmitted] = useState(false);

  const handleSubmit = (e: FormEvent<HTMLFormElement>) => {
    // 실제 구독 저장과 발송은 v2 범위이므로 서버로 보내지 않는다.
    e.preventDefault();
    setSubmitted(true);
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
            type="email"
            required
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            placeholder="이메일 주소"
            aria-label="이메일 주소"
            className="flex-1 rounded-xl border border-line-strong px-4 py-3"
          />
          <button type="submit" className="rounded-xl bg-primary px-5 py-3 font-semibold text-white hover:bg-primary-hover">
            구독 신청하기
          </button>
        </form>

        {submitted && (
          <p role="status" className="mt-3 text-sm text-label-neutral">
            실제 구독과 메일 발송은 v2에서 제공됩니다. 지금은 예시 화면만 보여드립니다.
          </p>
        )}
        <p className="mt-2 text-xs text-label-assistive">
          구독 신청 시 서비스 안내 목적의 메일 수신에 동의하는 것으로 간주됩니다.
        </p>

        <div className="mt-6 rounded-xl bg-bg-alt p-4 text-sm text-label-neutral">
          <p className="text-xs font-semibold text-label-alternate">받게 될 이메일 미리보기 (예시)</p>
          <p className="mt-2 font-semibold text-label-strong">[아침 시장 전망] 오늘의 시장 브리핑</p>
          <p className="mt-2">오늘의 시장 전망과 뉴스 Top 5 요약을 한 통에 담아 보내드립니다.</p>
          <p className="mt-2 text-xs text-label-alternate">투자 참고용이며 투자 권유가 아닙니다. 최종 판단과 책임은 본인에게 있습니다.</p>
        </div>
      </div>
    </section>
  );
}
