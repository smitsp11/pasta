import type { DemoData } from "../../types";
import northwind from "../iris_demo.json";
import ikea from "./ikea.json";

export interface Target { id: string; label: string; hosts: string[]; demo: DemoData }

/** Hardcoded demo targets. The URL typed on screen 1 is matched by hostname; anything else plays the fictional store. */
export const TARGETS: Target[] = [
  { id: "ikea", label: "IKEA Canada", hosts: ["ikea.com", "ikea.ca"], demo: ikea as unknown as DemoData },
  { id: "northwind", label: "Northwind Outfitters (fictional)", hosts: ["northwindoutfitters.com"], demo: northwind as unknown as DemoData },
];

export const DEFAULT_TARGET = TARGETS[0];

export function hostOf(input: string): string {
  const s = input.trim();
  if (!s) return "";
  try { return new URL(/^https?:\/\//i.test(s) ? s : `https://${s}`).hostname.toLowerCase(); } catch { return s.toLowerCase(); }
}

export function targetFor(input: string): Target {
  const host = hostOf(input);
  return TARGETS.find(t => t.hosts.some(h => host === h || host.endsWith(`.${h}`))) ?? DEFAULT_TARGET;
}

export const targetById = (id: string | null) => TARGETS.find(t => t.id === id) ?? DEFAULT_TARGET;
