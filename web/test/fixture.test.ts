import demo from "../src/data/iris_demo.json";
it("fixture is internally consistent", () => {
  const personaIds = new Set(demo.personas.map(p => p.id));
  const runIds = new Set(demo.runs.map(r => r.run_id));
  expect(demo.personas).toHaveLength(8);
  for (const p of demo.personas) expect(runIds.has(p.run_id)).toBe(true);
  for (const r of demo.runs) expect(personaIds.has(r.persona_id)).toBe(true);
  const pair = demo.personas.filter(p => p.pair_id);
  expect(pair).toHaveLength(2);
  const [a, b] = pair;
  expect(a.config.device).not.toBe(b.config.device);
  expect(a.config.identity).toBe(b.config.identity); expect(a.config.country).toBe(b.config.country);
  for (const f of demo.findings) expect(Object.keys(demo.affected)).toContain(f.id);
  expect(demo.sources.map(s => s.id)).toEqual(demo.reads.map(r => r.source_id));
});
