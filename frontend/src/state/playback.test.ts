import { describe, expect, it } from "vitest";
import { nextStepIndex, PLAYBACK_STEPS } from "./playback";

describe("playback steps", () => {
  it("cycles through every step and wraps around", () => {
    let index = 0;
    const seen: string[] = [];
    for (let i = 0; i < PLAYBACK_STEPS.length; i++) {
      seen.push(PLAYBACK_STEPS[index]);
      index = nextStepIndex(index);
    }
    expect(seen).toEqual(PLAYBACK_STEPS);
    expect(index).toBe(0);
  });
});
