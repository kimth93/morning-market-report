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
  await expect(page.getByRole("button", { name: "지금 생성하기" })).toHaveCount(0);
});

test("shows a readable error when the sample report is missing", async ({ page }) => {
  await mockReport(page, 404);
  await page.goto("/");

  await expect(page.getByRole("alert")).toContainText("보고서를 불러오지 못했습니다");
});

test("subscribing requires consent and then shows the review message", async ({ page }) => {
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
  await page.getByRole("button", { name: "신청하기" }).click();
  // 동의하지 않으면 브라우저 검증에 막혀 제출되지 않는다.
  await expect(page.getByRole("status")).toHaveCount(0);

  await consent.check();
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
