import type { StageName, StreamItem } from "../types";
import type { Cue } from "../data/script";

export class Player {
  private i = 0; private timer: ReturnType<typeof setTimeout> | null = null; private t0 = 0; private elapsed = 0;
  private cues: Cue[]; private dispatch: (it: StreamItem) => void; private opts: { speed: number };
  constructor(cues: Cue[], dispatch: (it: StreamItem) => void, opts: { speed: number } = { speed: 1 }) { this.cues = cues; this.dispatch = dispatch; this.opts = opts; }
  get done() { return this.i >= this.cues.length; }
  play() { if (this.timer || this.done) return; this.t0 = performance.now() - this.elapsed / this.opts.speed; this.tick(); }
  pause() { if (this.timer) clearTimeout(this.timer); this.timer = null; this.elapsed = (performance.now() - this.t0) * this.opts.speed; }
  setSpeed(speed: number) { const playing = !!this.timer; this.pause(); this.opts.speed = speed; if (playing) this.play(); }
  seekToStage(name: StageName) { this.pause(); while (this.i < this.cues.length) { const c = this.cues[this.i++]; this.dispatch(c.item); if (c.item.type === "stage" && c.item.name === name) break; } this.elapsed = this.cues[this.i - 1]?.t ?? 0; }
  private tick = () => {
    this.timer = null;
    const now = (performance.now() - this.t0) * this.opts.speed;
    while (this.i < this.cues.length && this.cues[this.i].t <= now) this.dispatch(this.cues[this.i++].item);
    if (this.done) return;
    this.timer = setTimeout(this.tick, Math.max(0, (this.cues[this.i].t - now) / this.opts.speed));
  };
}
