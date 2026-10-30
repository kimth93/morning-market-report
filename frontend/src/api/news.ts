export type Risk = "low" | "medium" | "high";

export interface NewsItem {
  title: string;
  source: string;
  date: string;
  url: string;
  summary: string;
  hallucination_risk: Risk;
}

export interface GenerateResponse {
  news_items: NewsItem[];
  market_outlook: string;
  investment_points: string[];
  generated_at: string;
}

export class ApiError extends Error {
  constructor(message: string) {
    super(message);
    this.name = "ApiError";
  }
}

export const API_BASE: string = import.meta.env.VITE_API_BASE ?? "http://127.0.0.1:8000";

export async function generateNews(fetchImpl: typeof fetch = fetch): Promise<GenerateResponse> {
  let response: Response;
  try {
    response = await fetchImpl(`${API_BASE}/api/news/generate`, { method: "POST" });
  } catch {
    throw new ApiError("백엔드 서버에 연결할 수 없습니다");
  }

  if (!response.ok) {
    throw new ApiError(await readErrorMessage(response));
  }
  return (await response.json()) as GenerateResponse;
}

async function readErrorMessage(response: Response): Promise<string> {
  try {
    const body = (await response.json()) as { detail?: unknown };
    if (typeof body.detail === "string") return body.detail;
  } catch {
    // 본문이 JSON이 아니면 상태 코드로 대신한다.
  }
  return `HTTP ${response.status}`;
}
