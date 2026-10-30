const PRINCIPLES = [
  { no: "01", title: "할루시네이션 금지", body: "원문에 없는 수치·통계·예측을 생성하지 않습니다." },
  { no: "02", title: "단정성 제어", body: "직접적 투자 권유 없이 조건부 표현만 사용합니다." },
  { no: "03", title: "편향성 제어", body: "금융·IT·바이오·에너지 등 섹터를 고르게 다룹니다." },
  { no: "04", title: "출처 명시", body: "제목·언론사·발행일·원문 링크를 함께 표기합니다." },
];

export default function TrustPrinciples() {
  return (
    <section className="pb-10">
      <h2 className="text-xl font-bold text-label-strong">신뢰성 규율</h2>
      <p className="mt-1 text-sm text-label-alternate">
        금융 규제 리스크를 최소화하기 위해 모든 요약은 아래 4가지 원칙을 따릅니다.
      </p>
      <ul className="mt-4 grid gap-4 sm:grid-cols-2">
        {PRINCIPLES.map((p) => (
          <li key={p.no} className="rounded-2xl border border-line bg-white p-5">
            <p className="text-xs font-bold text-primary">{p.no}</p>
            <p className="mt-1 font-semibold text-label-strong">{p.title}</p>
            <p className="mt-1 text-sm text-label-neutral">{p.body}</p>
          </li>
        ))}
      </ul>
    </section>
  );
}
