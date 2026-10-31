// 구독 신청은 Netlify Forms로 보낸다. 서버 코드가 없으므로 Netlify가 폼 데이터를 받아 대시보드에 쌓는다.
export const SUBSCRIPTION_FORM_NAME = "subscribe";

export interface SubscriptionInput {
  name: string;
  email: string;
  consent: boolean;
}

export async function submitSubscription(input: SubscriptionInput, fetchImpl: typeof fetch = fetch): Promise<void> {
  const body = new URLSearchParams({
    "form-name": SUBSCRIPTION_FORM_NAME,
    name: input.name,
    email: input.email,
    consent: input.consent ? "on" : "",
    "bot-field": "",
  });

  let response: Response;
  try {
    response = await fetchImpl("/", {
      method: "POST",
      headers: { "Content-Type": "application/x-www-form-urlencoded" },
      body: body.toString(),
    });
  } catch {
    throw new Error("신청을 보내지 못했습니다. 잠시 후 다시 시도해 주세요");
  }
  if (!response.ok) {
    throw new Error("신청을 보내지 못했습니다. 잠시 후 다시 시도해 주세요");
  }
}
