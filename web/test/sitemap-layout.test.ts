import { layoutNodes } from "../src/screens/learning/layout";
it("places nodes left-to-right by depth with journeys on the right edge and no two nodes at the same point", () => {
  const nodes = [{ path: "/", parent: null, journey: null }, { path: "/a", parent: "/", journey: 1 }, { path: "/a/b", parent: "/a", journey: null }, { path: "/c", parent: "/", journey: null }, { path: "/a/b/d", parent: "/a/b", journey: 2 }];
  const pos = layoutNodes(nodes);
  expect(pos["/"].x).toBe(10);
  expect(pos["/a"].x).toBeGreaterThan(pos["/"].x); expect(pos["/a/b/d"].x).toBeGreaterThan(pos["/a/b"].x);
  const pts = new Set(Object.values(pos).map(p => `${p.x},${p.y}`)); expect(pts.size).toBe(5);
});
