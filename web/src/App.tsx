import { useEffect, useRef } from "react";
import { AnimatePresence, motion } from "motion/react";
import { TopBar } from "./components/TopBar";
import { PixelDissolve } from "./primitives/PixelDissolve";
import { counts } from "./state/reducer";
import { usePlayer } from "./state/usePlayer";
import { Input } from "./screens/Input";
import { Learning } from "./screens/Learning";
import { Brief } from "./screens/Brief";
import { Swarm } from "./screens/Swarm";
import { Report } from "./screens/Report";

function Stage({ id, children }: { id: string; children: React.ReactNode }) {
  const ref = useRef<HTMLDivElement>(null);
  // Wait for the hero to finish collapsing (0.6s) before scrolling, or the target shifts under the sticky bar.
  useEffect(() => { const id = setTimeout(() => ref.current?.scrollIntoView?.({ behavior: "smooth", block: "start" }), 650); return () => clearTimeout(id); }, []);
  return (
    <motion.div ref={ref} id={id} initial={{ opacity: 0 }} animate={{ opacity: 1 }} transition={{ duration: 0.3 }} style={{ scrollMarginTop: 64 }}>
      <PixelDissolve trigger={id} duration={0.6}>{children}</PixelDissolve>
    </motion.div>);
}

export default function App() {
  const { state, target, runNo, start } = usePlayer();
  const run = `${target.id}:${runNo}`;   // re-keys the stages so a new run re-enters from the top
  const cached = new URLSearchParams(location.search).get("demo") === "cached";
  return (
    <div style={{ minHeight: "100vh", display: "flex", flexDirection: "column" }}>
      <TopBar stage={state.stage} sessions={counts(state).total} cached={cached} hasBrief={state.personas.length > 0 && state.stage === "explore"} />
      <main style={{ flex: 1 }}>
        <Input onRun={url => { window.scrollTo({ top: 0, behavior: "smooth" }); start(url); }} collapsed={state.stage !== "idle"} />
        <AnimatePresence>
          {state.stage !== "idle" && <Stage key={`learn-${run}`} id="learn"><Learning state={state} /></Stage>}
          {state.personas.length > 0 && <Stage key={`brief-${run}`} id="brief"><Brief personas={state.personas} stressTests={state.stress_tests} sources={state.sources} /></Stage>}
          {Object.keys(state.feeds).length > 0 && <Stage key={`swarm-${run}`} id="swarm"><Swarm state={state} /></Stage>}
          {state.scorecard && <Stage key={`report-${run}`} id="report"><Report scorecard={state.scorecard} findings={state.findings} affected={state.affected} personas={state.personas} feeds={state.feeds} sources={state.sources} journeys={state.site?.journeys ?? []} /></Stage>}
        </AnimatePresence>
      </main>
    </div>);
}
