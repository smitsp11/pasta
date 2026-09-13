import { buildScript } from "../src/data/script";
import demo from "../src/data/iris_demo.json";
it("orders stages and spaces items per the choreography", () => {
  const s = buildScript(demo as any);
  const types = s.map(x => x.item.type);
  const stageNames = s.filter(x => x.item.type === "stage").map(x => (x.item as any).name);
  expect(stageNames).toEqual(["explore", "run", "score", "done"]);
  expect(types.indexOf("source_read")).toBeGreaterThan(types.indexOf("stage"));
  expect(types.indexOf("site_model")).toBeGreaterThan(types.indexOf("source_read"));
  expect(types.indexOf("brief")).toBeGreaterThan(types.indexOf("site_model"));
  expect(types.lastIndexOf("run_result")).toBeLessThan(types.indexOf("result"));
  for (let i = 1; i < s.length; i++) expect(s[i].t).toBeGreaterThanOrEqual(s[i - 1].t);
  const starts = s.filter(x => x.item.type === "session_started");
  expect(starts).toHaveLength(8);
  const total = s[s.length - 1].t;
  expect(total).toBeGreaterThan(30_000); expect(total).toBeLessThan(120_000);
});
