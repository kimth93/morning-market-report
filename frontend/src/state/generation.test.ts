import { describe, expect, it } from "vitest";
import { initialState, reducer, GENERATION_STEPS } from "./generation";

const result = {
  news_items: [],
  market_outlook: "전망.",
  investment_points: ["a", "b", "c"],
  generated_at: "2026-07-08T09:00:00+00:00",
};

describe("generation reducer", () => {
  it("moves from idle to generating on start", () => {
    expect(reducer(initialState, { type: "start" }).phase).toBe("generating");
  });

  it("ignores a second start while generating", () => {
    const first = reducer(initialState, { type: "start" });
    expect(reducer(first, { type: "start" })).toBe(first);
  });

  it("cycles the step index only while generating", () => {
    const generating = reducer(initialState, { type: "start" });
    let state = generating;
    for (let i = 0; i < GENERATION_STEPS.length; i++) {
      state = reducer(state, { type: "stepTick" });
    }
    expect(state.stepIndex).toBe(0);
    expect(reducer(initialState, { type: "stepTick" })).toBe(initialState);
  });

  it("stores the result on success", () => {
    const state = reducer(reducer(initialState, { type: "start" }), { type: "succeed", result });
    expect(state.phase).toBe("done");
    expect(state.result).toEqual(result);
  });

  it("stores the message on failure", () => {
    const state = reducer(reducer(initialState, { type: "start" }), { type: "fail", message: "실패" });
    expect(state.phase).toBe("error");
    expect(state.error).toBe("실패");
  });

  it("returns to idle on reset", () => {
    const state = reducer(reducer(initialState, { type: "start" }), { type: "reset" });
    expect(state).toEqual(initialState);
  });
});
