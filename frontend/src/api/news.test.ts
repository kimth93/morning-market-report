import { describe, expect, it } from "vitest";
import { ApiError, API_BASE, generateNews, type GenerateResponse } from "./news";

const payload: GenerateResponse = {
  news_items: [
    {
      title: "코스피 급락",
      source: "한국경제",
      date: "2026-07-08",
      url: "https://www.hankyung.com/a",
      summary: "요약 문단.",
      hallucination_risk: "low",
    },
  ],
  market_outlook: "전망 문단.",
  investment_points: ["a", "b", "c"],
  generated_at: "2026-07-08T09:00:00+00:00",
};

function fakeFetch(response: Response | Error) {
  const calls: { url: string; init?: RequestInit }[] = [];
  const impl = async (url: string | URL | Request, init?: RequestInit) => {
    calls.push({ url: String(url), init });
    if (response instanceof Error) throw response;
    return response;
  };
  return { impl: impl as typeof fetch, calls };
}

describe("generateNews", () => {
  it("POSTs to the generate endpoint and returns the typed payload", async () => {
    const { impl, calls } = fakeFetch(new Response(JSON.stringify(payload), { status: 200 }));

    const result = await generateNews(impl);

    expect(result).toEqual(payload);
    expect(calls[0].url).toBe(`${API_BASE}/api/news/generate`);
    expect(calls[0].init?.method).toBe("POST");
  });

  it("throws ApiError with the backend detail on a 502", async () => {
    const body = JSON.stringify({ detail: "요약 검증 실패: 문단 수" });
    const { impl } = fakeFetch(new Response(body, { status: 502 }));

    await expect(generateNews(impl)).rejects.toMatchObject({
      name: "ApiError",
      message: "요약 검증 실패: 문단 수",
    });
  });

  it("throws ApiError when the network fails", async () => {
    const { impl } = fakeFetch(new TypeError("Failed to fetch"));

    await expect(generateNews(impl)).rejects.toBeInstanceOf(ApiError);
  });
});
