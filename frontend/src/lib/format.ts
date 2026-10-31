import type { Risk } from "../api/news";

export function formatDate(isoDate: string): string {
  const match = /^(\d{4}-\d{2}-\d{2})/.exec(isoDate);
  return match ? match[1] : isoDate;
}

export function safeHttpUrl(url: string): string | null {
  try {
    const parsed = new URL(url);
    return parsed.protocol === "http:" || parsed.protocol === "https:" ? parsed.href : null;
  } catch {
    return null;
  }
}

export const RISK_LABEL: Record<Risk, string> = {
  low: "위험 낮음",
  medium: "위험 보통",
  high: "위험 높음",
};
