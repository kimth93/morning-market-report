import { ApiError, API_BASE } from "./news";

export interface SignupInput {
  email: string;
  name: string;
}

export interface SignupResponse {
  status: "success";
  subscription_id: string;
}

export async function signupSubscriber(
  input: SignupInput,
  fetchImpl: typeof fetch = fetch,
): Promise<SignupResponse> {
  let response: Response;
  try {
    response = await fetchImpl(`${API_BASE}/api/subscription/signup`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(input),
    });
  } catch {
    throw new ApiError("백엔드 서버에 연결할 수 없습니다");
  }

  if (!response.ok) {
    throw new ApiError(await readDetail(response));
  }
  return (await response.json()) as SignupResponse;
}

async function readDetail(response: Response): Promise<string> {
  try {
    const body = (await response.json()) as { detail?: unknown };
    if (typeof body.detail === "string") return body.detail;
  } catch {
    // JSON이 아니면 상태 코드로 대신한다.
  }
  return `HTTP ${response.status}`;
}
