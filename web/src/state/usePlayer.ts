import { useEffect, useMemo, useReducer, useRef, useState } from "react";
import demo from "../data/iris_demo.json";
import { buildScript } from "../data/script";
import { initialState, reduce } from "./reducer";
import { Player } from "./player";
import type { StageName } from "../types";

export function usePlayer() {
  const [state, dispatch] = useReducer(reduce, demo as any, initialState);
  const params = useMemo(() => new URLSearchParams(location.search), []);
  const speed = Number(params.get("speed") ?? 1);
  const [playing, setPlaying] = useState(false);
  const player = useRef<Player | null>(null);
  useEffect(() => { player.current = new Player(buildScript(demo as any), dispatch, { speed }); return () => player.current?.pause(); }, [speed]);
  useEffect(() => { const st = params.get("stage") as StageName | null; if (st) { player.current?.seekToStage(st); setPlaying(false); } }, [params]);
  return { state, playing, start: () => { player.current?.play(); setPlaying(true); }, pause: () => { player.current?.pause(); setPlaying(false); } };
}
