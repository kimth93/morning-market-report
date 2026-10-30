import { expect, test, type Page, type Route } from "@playwright/test";

// 백엔드 응답은 결정적으로 모킹한다. 실제 호출 검증은 backend/tests/test_live_e2e.py가 맡는다.
const API = "http://127.0.0.1:8000";

const report = {
  news_items: Array.from({ length: 5 }, (_, i) => ({
    title: `테스트 기사 ${i + 1}`,
    source: "한국경제",
    date: "2026-07-08",
    url: `https://www.hankyung.com/article/${i + 1}`,
    summary: `요약 문단 ${i + 1}. 주목할 만한 흐름이다.`,
    hallucination_risk: i % 2 === 0 ? "low" : "medium",
  })),
  market_outlook: "기술주 중심으로 변동성이 이어질 가능성이 있습니다.",
  investment_points: ["반도체 흐름 관찰", "환율 변동 확인", "금리 발표 일정 체크"],
  generated_at: "2026-07-08T09:00:00+09:00",
};

async function mockGenerate(page: Page, options: { delayMs?: number; failWith?: string } = {}) {
  await page.route(`${API}/api/news/generate`, async (route: Route) => {
    if (options.delayMs) await new Promise((r) => setTimeout(r, options.delayMs));
    if (options.failWith) {
      await route.fulfill({ status: 502, contentType: "application/json", body: JSON.stringify({ detail: options.failWith }) });
      return;
    }
    await route.fulfill({ status: 200, contentType: "application/json", body: JSON.stringify(report) });
  });
}

test("shows the disclaimer and generates the full report", async ({ page }) => {
  await mockGenerate(page, { delayMs: 4000 });
  await page.goto("/");

  await expect(page.getByRole("note")).toContainText("투자는 본인의 판단으로 하시기 바랍니다");

  await page.getByRole("button", { name: "지금 생성하기" }).click();
  await expect(page.getByRole("status")).toContainText("수집하고 있습니다");
  await expect(page.getByRole("button", { name: "지금 생성하기" })).toBeDisabled();

  await expect(page.getByText("보고서 생성 완료")).toBeVisible();
  await expect(page.getByRole("heading", { name: "오늘의 시장 전망" })).toBeVisible();
  await expect(page.getByRole("heading", { name: "경제·증권 뉴스 Top 5" })).toBeVisible();
  await expect(page.getByRole("heading", { level: 3 })).toHaveCount(5);
  await expect(page.getByRole("link", { name: "원문 보기" })).toHaveCount(5);
  await expect(page.getByRole("link", { name: "원문 보기" }).first()).toHaveAttribute("href", /^https:\/\//);
  await expect(page.getByText("위험 낮음").first()).toBeVisible();
});

test("shows a retryable error when generation fails", async ({ page }) => {
  await mockGenerate(page, { failWith: "요약 검증 실패: 문단 수" });
  await page.goto("/");

  await page.getByRole("button", { name: "지금 생성하기" }).click();
  await expect(page.getByRole("alert")).toContainText("요약 검증 실패: 문단 수");
  await expect(page.getByRole("button", { name: "다시 시도" })).toBeVisible();
});

test("subscribing shows a success message and the preview uses the generated report", async ({ page }) => {
  await mockGenerate(page);
  let signupBody: unknown = null;
  await page.route(`${API}/api/subscription/signup`, async (route: Route) => {
    signupBody = route.request().postDataJSON();
    await route.fulfill({
      status: 200,
      contentType: "application/json",
      body: JSON.stringify({ status: "success", subscription_id: "42" }),
    });
  });
  await page.goto("/");

  await expect(page.getByText("'지금 생성하기'로 보고서를 만들면")).toBeVisible();
  await page.getByRole("button", { name: "지금 생성하기" }).click();
  await expect(page.getByText("보고서 생성 완료")).toBeVisible();

  await expect(page.getByText("[아침 시장 전망] 오늘의 시장 브리핑")).toBeVisible();
  // 전망 문장은 결과 화면과 미리보기에 한 번씩 나온다.
  await expect(page.getByText(report.market_outlook)).toHaveCount(2);

  await page.getByLabel("이름").fill("김투자");
  await page.getByLabel("이메일 주소").fill("reader@example.com");
  await page.getByRole("button", { name: "구독 신청하기" }).click();

  await expect(page.getByRole("status")).toContainText("구독 신청이 완료되었습니다 (구독 ID: 42)");
  expect(signupBody).toEqual({ email: "reader@example.com", name: "김투자" });
});

test("the report stays one column with no horizontal scroll on a phone", async ({ page }) => {
  await page.setViewportSize({ width: 400, height: 860 });
  await mockGenerate(page);
  await page.goto("/");
  await page.getByRole("button", { name: "지금 생성하기" }).click();
  await expect(page.getByText("보고서 생성 완료")).toBeVisible();

  const overflow = await page.evaluate(() => document.documentElement.scrollWidth - document.documentElement.clientWidth);
  expect(overflow).toBeLessThanOrEqual(0);
});
