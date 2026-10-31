import { describe, expect, it } from "vitest";
import { submitSubscription, SUBSCRIPTION_FORM_NAME } from "./subscription";

describe("submitSubscription", () => {
  it("posts the form fields as urlencoded data to the static site root", async () => {
    const calls: { url: string; init?: RequestInit }[] = [];
    const fakeFetch = (async (url: string, init?: RequestInit) => {
      calls.push({ url, init });
      return new Response(null, { status: 200 });
    }) as typeof fetch;

    await submitSubscription({ name: "김투자", email: "reader@example.com", consent: true }, fakeFetch);

    expect(calls[0].url).toBe("/");
    const body = new URLSearchParams(String(calls[0].init?.body));
    expect(body.get("form-name")).toBe(SUBSCRIPTION_FORM_NAME);
    expect(body.get("email")).toBe("reader@example.com");
    expect(body.get("consent")).toBe("on");
    expect(body.get("bot-field")).toBe("");
  });

  it("throws when the form submission is rejected", async () => {
    const fakeFetch = (async () => new Response(null, { status: 500 })) as typeof fetch;

    await expect(
      submitSubscription({ name: "김", email: "a@b.co", consent: true }, fakeFetch),
    ).rejects.toThrow("신청을 보내지 못했습니다");
  });
});
