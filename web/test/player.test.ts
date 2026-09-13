import { Player } from "../src/state/player";
it("dispatches cues on the clock, honours speed, and can seek to a stage", () => {
  vi.useFakeTimers();
  const seen: string[] = [];
  const cues = [{ t: 0, item: { type: "stage", name: "explore" } }, { t: 1000, item: { type: "stage", name: "run" } }, { t: 3000, item: { type: "stage", name: "done" } }] as any;
  const p = new Player(cues, it => seen.push((it as any).name), { speed: 2 });
  p.play();
  vi.advanceTimersByTime(499); expect(seen).toEqual(["explore"]);
  vi.advanceTimersByTime(2); expect(seen).toEqual(["explore", "run"]);
  vi.advanceTimersByTime(1000); expect(seen).toEqual(["explore", "run", "done"]);
  const seen2: string[] = []; const p2 = new Player(cues, it => seen2.push((it as any).name), { speed: 1 });
  p2.seekToStage("run"); expect(seen2).toEqual(["explore", "run"]);   // seek dispatches everything up to and including that stage, instantly
  vi.useRealTimers();
});
