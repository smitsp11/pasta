# Iris — front end

Fixture-driven, single-page React app that plays the five-stage show (Input → Learning → Brief → Swarm → Report).
No backend calls: a `Player` replays an authored demo script (`src/data/iris_demo.json` → `src/data/script.ts`)
through a pure reducer, and every screen renders from `RunState`. A live websocket can replace the Player later
without touching the screens.

Production: https://iris-tau-two.vercel.app

## Run

```bash
npm install
npm run dev          # http://localhost:5173
npm test             # vitest unit tests (reducer, script, textures, screens)
npm run e2e          # playwright: builds, previews on :4173, plays the show, screenshots each stage into e2e/screens/
npm run build
```

## URL parameters

| Param | Effect |
|---|---|
| `?speed=6` | Play the show 6× faster (any number; default 1, ~60s show). |
| `?stage=run` | Seek instantly to a stage marker (`explore`, `run`, `score`, `done`) for rehearsal or screenshots. |
| `?demo=cached` | Show the `[ CACHED ]` pill in the top bar (stage fallback mode). |

## Deploy

```bash
vercel --prod --yes     # project smitsp11s-projects/iris; vercel.json pins framework=vite, output=dist
```

## Design sources

Tokens, motion vocabulary and choreography timings are in `docs/design-brief.md`; verbatim per-frame styles are in
`design/EXTRACTION.md`, extracted from the Claude Design exports in `design/frames/*.dc.html` (the `.dc.html` wins on
conflict). The implementation plan is `docs/superpowers/plans/2026-09-13-iris-frontend.md`.
