import type { SiteNode } from "../../types";
export type Pos = { x: number; y: number };   // percent of the graph box
/** Depth-column layout: root at x=10, deeper columns spread to x=78 (labels extend right); siblings spread vertically 12..88. */
export function layoutNodes(nodes: SiteNode[]): Record<string, Pos> {
  const depth: Record<string, number> = {};
  const d = (p: string): number => { if (depth[p] != null) return depth[p]; const n = nodes.find(x => x.path === p); depth[p] = n?.parent ? d(n.parent) + 1 : 0; return depth[p]; };
  nodes.forEach(n => d(n.path));
  const maxD = Math.max(0, ...Object.values(depth));
  const cols: Record<number, string[]> = {};
  nodes.forEach(n => (cols[depth[n.path]] ??= []).push(n.path));
  const pos: Record<string, Pos> = {};
  Object.entries(cols).forEach(([k, paths]) => {
    const x = maxD === 0 ? 10 : 10 + (68 * Number(k)) / maxD;
    paths.forEach((p, i) => { pos[p] = { x, y: paths.length === 1 ? 50 : 12 + (76 * i) / (paths.length - 1) }; });
  });
  return pos;
}
export const edgePath = (a: Pos, b: Pos) => `M ${a.x} ${a.y} C ${a.x + (b.x - a.x) * 0.45} ${a.y}, ${a.x + (b.x - a.x) * 0.55} ${b.y}, ${b.x} ${b.y}`;
