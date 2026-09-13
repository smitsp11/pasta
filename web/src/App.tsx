import { TopBar } from "./components/TopBar";
import { usePlayer } from "./state/usePlayer";
import { counts } from "./state/reducer";
import { Input } from "./screens/Input";
export default function App() {
  const { state, start } = usePlayer();
  const cached = new URLSearchParams(location.search).get("demo") === "cached";
  return (
    <div style={{ minHeight: "100vh", display: "flex", flexDirection: "column" }}>
      <TopBar stage={state.stage} sessions={counts(state).total} cached={cached} hasBrief={state.personas.length > 0} />
      <main style={{ flex: 1 }}>
        <Input onRun={() => start()} collapsed={state.stage !== "idle"} />
      </main>
    </div>);
}
