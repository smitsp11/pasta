import { TARGETS, targetFor, hostOf } from "../src/data/targets";
import { validateDemo } from "../src/data/validate";

describe.each(TARGETS.map(t => [t.id, t] as const))("target %s", (_id, t) => {
  it("is internally consistent", () => { expect(validateDemo(t.demo)).toEqual([]); });
});

it("matches typed urls to targets and falls back to the fictional store", () => {
  expect(hostOf("zara.com/us")).toBe("zara.com");
  expect(hostOf("https://www.ikea.com/ca/en/")).toBe("www.ikea.com");
  expect(targetFor("https://northwindoutfitters.com").id).toBe("northwind");
  expect(targetFor("https://example.org").id).toBe(TARGETS[0].id);
  expect(targetFor("").id).toBe(TARGETS[0].id);
});
