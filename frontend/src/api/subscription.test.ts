import { describe, expect, it } from "vitest";
import { ApiError, API_BASE } from "./news";
import { signupSubscriber } from "./subscription";

describe("signupSubscriber", () => {
  it("posts email and name as JSON and returns the subscription id", async () => {
    const calls: { url: string; init?: RequestInit }[] = [];
    const fakeFetch = (async (url: string, init?: RequestInit) => {
      calls.push({ url, init });
      return new Response(JSON.stringify({ status: "success", subscription_id: "7" }), { status: 200 });
    }) as typeof fetch;

    const result = await signupSubscriber({ email: "a@b.co", name: "김" }, fakeFetch);

    expect(result).toEqual({ status: "success", subscription_id: "7" });
    expect(calls[0].url).toBe(`${API_BASE}/api/subscription/signup`);
    expect(JSON.parse(String(calls[0].init?.body))).toEqual({ email: "a@b.co", name: "김" });
  });

  it("throws ApiError with the backend detail on rejection", async () => {
    const fakeFetch = (async () =>
      new Response(JSON.stringify({ detail: "이메일 형식이 올바르지 않습니다" }), { status: 422 })) as typeof fetch;

    await expect(signupSubscriber({ email: "x", name: "김" }, fakeFetch)).rejects.toBeInstanceOf(ApiError);
  });
});
