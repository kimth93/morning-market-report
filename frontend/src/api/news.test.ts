import { describe, expect, it } from "vitest";
import { loadSnapshot, SNAPSHOT_URL, type Report } from "./news";

const report: Report = {
  news_items: [
    {
      title: "코스피 급락",
      source: "한국경제",
      date: "2026-10-31",
      url: "https://www.hankyung.com/a",
      summary: "요약 문단.",
      hallucination_risk: "low",
    },
  ],
  market_outlook: "전망 문단.",
  investment_points: ["a", "b", "c"],
  generated_at: "2026-10-31T07:00:00+00:00",
  source_note: "예시 보고서입니다.",
};

describe("loadSnapshot", () => {
  it("reads the static report file", async () => {
    const calls: string[] = [];
    const fakeFetch = (async (url: string) => {
      calls.push(url);
      return new Response(JSON.stringify(report), { status: 200 });
    }) as typeof fetch;

    const result = await loadSnapshot(fakeFetch);

    expect(result).toEqual(report);
    expect(calls[0]).toBe(SNAPSHOT_URL);
  });

  it("throws a readable error when the file is missing", async () => {
    const fakeFetch = (async () => new Response("not found", { status: 404 })) as typeof fetch;

    await expect(loadSnapshot(fakeFetch)).rejects.toThrow("보고서를 불러오지 못했습니다");
  });
});
