export type Risk = "low" | "medium" | "high";

export interface NewsItem {
  title: string;
  source: string;
  date: string;
  url: string;
  summary: string;
  hallucination_risk: Risk;
}

export interface Report {
  news_items: NewsItem[];
  market_outlook: string;
  investment_points: string[];
  generated_at: string;
  source_note: string;
}

export const SNAPSHOT_URL = "/report.json";

export async function loadSnapshot(fetchImpl: typeof fetch = fetch): Promise<Report> {
  let response: Response;
  try {
    response = await fetchImpl(SNAPSHOT_URL);
  } catch {
    throw new Error("보고서를 불러오지 못했습니다");
  }
  if (!response.ok) {
    throw new Error("보고서를 불러오지 못했습니다");
  }
  return (await response.json()) as Report;
}
