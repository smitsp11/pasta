import { initialState, reduce } from "../src/state/reducer";
import { buildScript } from "../src/data/script";
import demo from "../src/data/iris_demo.json";

it("folds the whole script into a finished state", () => {
  const s = buildScript(demo as any).reduce((st, c) => reduce(st, c.item), initialState(demo as any));
  expect(s.stage).toBe("done");
  expect(Object.keys(s.read)).toHaveLength(9);
  expect(s.nodes).toHaveLength(7);
  expect(s.personas).toHaveLength(8);
  expect(Object.keys(s.feeds)).toHaveLength(8);
  expect(s.feeds["r4"].status).toBe("stalled"); expect(s.feeds["r8"].status).toBe("harness_error"); expect(s.feeds["r1"].status).toBe("completed");
  expect(s.feeds["r4"].last_action).toBe("overlay keeps intercepting clicks");
  expect(s.scorecard?.overall).toBe(58); expect(s.findings).toHaveLength(4);
});
it("reticle focus follows the latest event, and a retry replaces the feed", () => {
  let s = initialState(demo as any);
  const cfg = demo.personas[0].config as any;
  s = reduce(s, { type: "session_started", run_id: "r1", session_id: "a", journey_id: "j", config: cfg, viewer_url: "v", replay_url: "r", hls_url: "h", timestamp: "" });
  expect(s.focus).toBe("r1");
  s = reduce(s, { type: "session_started", run_id: "r1", session_id: "b", journey_id: "j", config: cfg, viewer_url: "v2", replay_url: "r", hls_url: "h", timestamp: "" });
  expect(Object.keys(s.feeds)).toEqual(["r1"]); expect(s.feeds["r1"].session_id).toBe("b");
});
