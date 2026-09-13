# Iris design exports

Exported from Claude Design on Sept 13. Source of truth for the UI build; `docs/design-brief.md` is the written spec.

- `frames/` — one self-contained HTML per screen (`*.dc.html`) plus `support.js`, the small template runtime the exports use (`{{ }}` bindings, `style-hover`, `sc-if`). Inline styles carry the exact tokens. `Learning B` and `Swarm B` are the mid-motion states used as animation before/after references.
- `assets/` — the dot-field background, the world-dots map, and the dithered computer illustrations.

View locally:

```bash
cd design/frames && python3 -m http.server 8787
# then open http://127.0.0.1:8787/Iris%2004%20Swarm.dc.html
```

Porting notes: markup is plain divs/spans with inline styles; every frame repeats the same top bar, so extract it once. Fonts: Instrument Serif, Inter, Geist Mono via Google Fonts. The runtime is not needed in the real app; the `{{ }}` bindings map onto React props.
