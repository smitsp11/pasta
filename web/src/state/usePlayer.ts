import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import { buildScript } from "../data/script";
import { targetById, targetFor, type Target } from "../data/targets";
import { initialState, reduce } from "./reducer";
import { Player } from "./player";
import type { RunState, StageName, StreamItem } from "../types";

/**
 * Owns the only timers in the app. `start(url)` picks the hardcoded target for that URL, resets state to that
 * target's demo, and plays its script. `?target=<id>&stage=<name>` seeks instantly (rehearsal / screenshots);
 * `?speed=` scales the clock.
 */
export function usePlayer() {
  const params = useMemo(() => new URLSearchParams(location.search), []);
  const speed = Number(params.get("speed") ?? 1) || 1;
  const [target, setTarget] = useState<Target>(() => targetById(params.get("target")));
  const [runNo, setRunNo] = useState(0);
  const [state, setState] = useState<RunState>(() => initialState(target.demo));
  const [playing, setPlaying] = useState(false);
  const player = useRef<Player | null>(null);
  const dispatch = useCallback((it: StreamItem) => setState(s => reduce(s, it)), []);

  const load = useCallback((t: Target) => {
    player.current?.pause();
    setTarget(t);
    setState(initialState(t.demo));
    player.current = new Player(buildScript(t.demo), dispatch, { speed });
    return player.current;
  }, [dispatch, speed]);

  useEffect(() => {
    const p = load(targetById(params.get("target")));
    const st = params.get("stage") as StageName | null;
    if (st) { p.seekToStage(st); setPlaying(false); }
    return () => p.pause();
  }, [load, params]);

  const start = useCallback((url: string) => { load(targetFor(url)).play(); setPlaying(true); setRunNo(n => n + 1); }, [load]);
  const pause = useCallback(() => { player.current?.pause(); setPlaying(false); }, []);
  return { state, target, playing, runNo, start, pause };
}
