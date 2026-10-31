import { expect, test, type Page, type Route } from "@playwright/test";

// 정적 PoC: 보고서는 /report.json에서 읽고, 신청은 Netlify Forms(POST /)로 보낸다.
const report = {
  news_items: Array.from({ length: 5 }, (_, i) => ({
    title: `테스트 기사 ${i + 1}`,
    source: "한국경제",
    date: "2026-10-31",
    url: `https://www.hankyung.com/article/${i + 1}`,
    summary: `요약 문단 ${i + 1}. 주목할 만한 흐름이다.`,
    hallucination_risk: i % 2 === 0 ? "low" : "medium",
  })),
  market_outlook: "기술주 중심으로 변동성이 이어질 가능성이 있습니다.",
  investment_points: ["반도체 흐름 관찰", "환율 변동 확인", "금리 발표 일정 체크"],
  generated_at: "2026-10-31T07:00:00+00:00",
  source_note: "개발자가 생성한 예시 보고서입니다. 실시간 생성 결과가 아닙니다.",
};

async function mockReport(page: Page, status = 200) {
  await page.route("**/report.json", async (route: Route) => {
    await route.fulfill({
      status,
      contentType: "application/json",
      body: status === 200 ? JSON.stringify(report) : "not found",
    });
  });
}

test("shows the disclaimer and the sample report without any generate button", async ({ page }) => {
  await mockReport(page);
  await page.goto("/");

  await expect(page.getByRole("note").first()).toContainText("투자는 본인의 판단으로 하시기 바랍니다");
  await expect(page.getByText("개발자가 생성한 예시 보고서입니다")).toBeVisible();
  await expect(page.getByRole("heading", { name: "오늘의 시장 전망" })).toBeVisible();
  await expect(page.getByRole("heading", { level: 3 })).toHaveCount(5);
  await expect(page.getByRole("link", { name: "원문 보기" })).toHaveCount(5);
  await expect(page.getByRole("button", { name: "지금 생성하기" })).toBeVisible();
});

test("지금 생성 replays the saved sample without calling any paid API", async ({ page }) => {
  let reportLoads = 0;
  await page.route("**/report.json", async (route: Route) => {
    reportLoads += 1;
    await route.fulfill({ status: 200, contentType: "application/json", body: JSON.stringify(report) });
  });
  // 유료 API 경로로 나가는 요청이 있으면 실패해야 한다.
  let externalCalls = 0;
  await page.route(/api\.anthropic\.com|naverapihub|127\.0\.0\.1:8000/, async (route: Route) => {
    externalCalls += 1;
    await route.abort();
  });
  await page.goto("/");
  const initialLoads = reportLoads;

  await page.getByRole("button", { name: "지금 생성하기" }).click();
  await expect(page.getByRole("status")).toContainText("수집하고 있습니다");
  await expect(page.getByRole("button", { name: "재생 중" })).toBeDisabled();

  await expect(page.getByRole("heading", { name: "오늘의 시장 전망" })).toBeVisible({ timeout: 10_000 });
  await expect(page.getByRole("button", { name: "지금 생성하기" })).toBeVisible();
  expect(reportLoads).toBeGreaterThan(initialLoads);
  expect(externalCalls).toBe(0);
});

test("shows a readable error when the sample report is missing", async ({ page }) => {
  await mockReport(page, 404);
  await page.goto("/");

  await expect(page.getByRole("alert")).toContainText("보고서를 불러오지 못했습니다");
});

test("the signup button stays disabled until consent is checked", async ({ page }) => {
  await mockReport(page);
  let posted: URLSearchParams | null = null;
  await page.route("**/", async (route: Route) => {
    if (route.request().method() !== "POST") return route.fallback();
    posted = new URLSearchParams(route.request().postData() ?? "");
    await route.fulfill({ status: 200, contentType: "text/html", body: "<html>ok</html>" });
  });
  await page.goto("/");

  await page.getByRole("textbox", { name: "이름", exact: true }).fill("김투자");
  await page.getByRole("textbox", { name: "이메일 주소", exact: true }).fill("reader@example.com");
  const consent = page.getByRole("checkbox");
  await expect(consent).not.toBeChecked();
  // 동의 전에는 신청 버튼이 비활성화되어 있어야 한다.
  await expect(page.getByRole("button", { name: "신청하기" })).toBeDisabled();

  await consent.check();
  await expect(page.getByRole("button", { name: "신청하기" })).toBeEnabled();
  await page.getByRole("button", { name: "신청하기" }).click();
  await expect(page.getByRole("status")).toContainText("신청이 접수되었습니다");
  expect(posted?.get("form-name")).toBe("subscribe");
  expect(posted?.get("email")).toBe("reader@example.com");
  expect(posted?.get("consent")).toBe("on");
});

test("the report stays one column with no horizontal scroll on a phone", async ({ page }) => {
  await page.setViewportSize({ width: 400, height: 860 });
  await mockReport(page);
  await page.goto("/");
  await expect(page.getByRole("heading", { name: "오늘의 시장 전망" })).toBeVisible();

  const overflow = await page.evaluate(() => document.documentElement.scrollWidth - document.documentElement.clientWidth);
  expect(overflow).toBeLessThanOrEqual(0);
});
