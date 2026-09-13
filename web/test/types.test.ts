import type { RunState, StreamItem } from "../src/types";
it("types compile", () => {
  const item: StreamItem = { type: "stage", name: "explore", timestamp: "2026-09-13T00:00:00Z" };
  const s: Partial<RunState> = { stage: "idle" };
  expect(item.type).toBe("stage"); expect(s.stage).toBe("idle");
});
