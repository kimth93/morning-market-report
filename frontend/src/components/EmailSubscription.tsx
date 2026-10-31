import { useState, type FormEvent } from "react";
import { submitSubscription } from "../api/subscription";

type Status =
  | { kind: "idle" }
  | { kind: "submitting" }
  | { kind: "success" }
  | { kind: "error"; message: string };

export default function EmailSubscription() {
  const [name, setName] = useState("");
  const [email, setEmail] = useState("");
  const [consent, setConsent] = useState(false);
  const [status, setStatus] = useState<Status>({ kind: "idle" });

  const handleSubmit = async (e: FormEvent<HTMLFormElement>) => {
    e.preventDefault();
    setStatus({ kind: "submitting" });
    try {
      await submitSubscription({ name, email, consent });
      setStatus({ kind: "success" });
    } catch (error) {
      setStatus({ kind: "error", message: error instanceof Error ? error.message : "알 수 없는 오류가 발생했습니다" });
    }
  };

  return (
    <section className="pb-10">
      <div className="rounded-2xl border border-line bg-white p-6 shadow-elev-1">
        <h2 className="text-xl font-bold text-label-strong">매일 아침 이메일로 받아보기 (신청)</h2>
        <p className="mt-1 text-sm text-label-neutral">
          이 기능은 포트폴리오 PoC입니다. 신청은 접수만 되며, 개발자가 확인해 승인한 주소에만 발송됩니다. 실제 발송은
          아직 시작되지 않았습니다.
        </p>

        <form onSubmit={handleSubmit} className="mt-4 space-y-3">
          <div className="flex flex-col gap-3 sm:flex-row">
            <input
              type="text"
              name="name"
              required
              value={name}
              onChange={(e) => setName(e.target.value)}
              placeholder="이름"
              aria-label="이름"
              className="rounded-xl border border-line-strong px-4 py-3"
            />
            <input
              type="email"
              name="email"
              required
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              placeholder="이메일 주소"
              aria-label="이메일 주소"
              className="flex-1 rounded-xl border border-line-strong px-4 py-3"
            />
          </div>
          <label className="flex items-start gap-2 text-sm text-label-neutral">
            <input
              type="checkbox"
              name="consent"
              required
              checked={consent}
              onChange={(e) => setConsent(e.target.checked)}
              className="mt-1"
            />
            <span>
              입력한 이름과 이메일을 신청 확인과 승인 후 발송 목적으로 수집하는 데 동의합니다. 보관 기간과 삭제 요청은
              아래 안내를 참고해 주세요.
            </span>
          </label>
          <button
            type="submit"
            disabled={status.kind === "submitting"}
            className="rounded-xl bg-primary px-5 py-3 font-semibold text-white hover:bg-primary-hover disabled:cursor-not-allowed disabled:bg-primary-bg-strong"
          >
            {status.kind === "submitting" ? "신청 중" : "신청하기"}
          </button>
        </form>

        {status.kind === "success" && (
          <p role="status" className="mt-3 text-sm font-semibold text-green-700">
            신청이 접수되었습니다. 개발자 승인 후 발송 대상에 포함됩니다.
          </p>
        )}
        {status.kind === "error" && (
          <p role="alert" className="mt-3 text-sm text-red-700">
            {status.message}
          </p>
        )}

        <div className="mt-6 rounded-xl bg-bg-alt p-4 text-sm text-label-neutral">
          <p className="font-semibold text-label-strong">개인정보 안내</p>
          <ul className="mt-2 list-disc space-y-1 pl-5">
            <li>수집 항목: 이름, 이메일 주소</li>
            <li>이용 목적: 신청 확인과 승인된 경우의 메일 발송</li>
            <li>보관 기간: 발송 프로젝트가 끝나거나 삭제 요청을 받을 때까지</li>
            <li>삭제 요청과 문의: 개발자에게 문의</li>
          </ul>
        </div>
      </div>
    </section>
  );
}
