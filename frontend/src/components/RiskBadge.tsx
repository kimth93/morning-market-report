import type { Risk } from "../api/news";
import { RISK_LABEL } from "../lib/format";

const STYLE: Record<Risk, string> = {
  low: "bg-bg-positive text-green-700",
  medium: "bg-bg-cautionary text-orange-700",
  high: "bg-red-50 text-red-700",
};

export default function RiskBadge({ level }: { level: Risk }) {
  return (
    <span className={`inline-flex items-center rounded-full px-2.5 py-1 text-xs font-semibold ${STYLE[level]}`}>
      {RISK_LABEL[level]}
    </span>
  );
}
