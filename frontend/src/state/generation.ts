import type { GenerateResponse } from "../api/news";

export type Phase = "idle" | "generating" | "done" | "error";

export const GENERATION_STEPS = [
  "뉴스를 수집하고 있습니다",
  "기사를 요약하고 있습니다",
  "시장 전망을 작성하고 있습니다",
];

export interface GenerationState {
  phase: Phase;
  result?: GenerateResponse;
  error?: string;
  stepIndex: number;
}

export type GenerationAction =
  | { type: "start" }
  | { type: "stepTick" }
  | { type: "succeed"; result: GenerateResponse }
  | { type: "fail"; message: string }
  | { type: "reset" };

export const initialState: GenerationState = { phase: "idle", stepIndex: 0 };

export function reducer(state: GenerationState, action: GenerationAction): GenerationState {
  switch (action.type) {
    case "start":
      // 이미 생성 중이면 무시해서 요청이 겹치지 않게 한다.
      if (state.phase === "generating") return state;
      return { phase: "generating", stepIndex: 0 };
    case "stepTick":
      if (state.phase !== "generating") return state;
      return { ...state, stepIndex: (state.stepIndex + 1) % GENERATION_STEPS.length };
    case "succeed":
      return { phase: "done", result: action.result, stepIndex: 0 };
    case "fail":
      return { phase: "error", error: action.message, stepIndex: 0 };
    case "reset":
      return initialState;
  }
}
