# Iris frame extraction (engineering reference)

Source: `design/frames/*.dc.html` (Claude Design exports). Values are verbatim. The large hand-drawn `<pre>` ASCII blocks are **not** reproduced here: the app generates ASCII textures from images (see `docs/design-brief.md` §6), so only their *styling* matters. When anything here conflicts with a `.dc.html`, the `.dc.html` wins.

| File | Stage |
|---|---|
| `Iris 01 Input.dc.html` | INPUT |
| `Iris Top Bar.dc.html` | top-bar spec sheet (2 variants) |
| `Iris 02 Learning.dc.html` / ` B` | LEARN (A / later state B) |
| `Iris 03 Brief.dc.html` | BRIEF |
| `Iris 04 Swarm.dc.html` / ` B` | SWARM (A / later state B) |
| `Iris 05 Report.dc.html` | REPORT |

---

## 0. Shared foundations

### 0.1 Fonts (identical in every frame)
```html
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Instrument+Serif:ital@0;1&family=Inter:wght@400;500;600&family=Geist+Mono:wght@400;500&display=swap" rel="stylesheet">
```
| Role | Stack |
|---|---|
| Display / logo / H1 | `'Instrument Serif', Georgia, serif` |
| Body / UI | `Inter, system-ui, sans-serif` |
| Mono / labels / ASCII | `'Geist Mono', ui-monospace, monospace` |

### 0.2 Colours
`#FAF7F2` paper · `#141414` ink · `#FF5A1F` orange · `#8A8580` muted · `#1F9D55` green · `#D93025` red · `#FFFFFF` white · `#E44B12` button hover.
Alphas used verbatim: ink `0.02 0.04 0.06 0.08 0.1 0.12 0.14 0.16 0.18 0.2 0.22 0.3 0.4 0.42 0.44 0.45 0.5`; orange `0.05 0.08 0.1 0.12 0.5 0.55`; red `0.1 0.3 0.5`; green `0.07 0.3 0.32 0.45 0.5`; `rgba(138,133,128,0.7)`; paper `0.85 0.9`.

Pastel gradient set (two-stop `linear-gradient`): `#FFD9CF` peach · `#F3E9D2` cream · `#E5DDF5` lilac · `#D8ECE3` mint. Angles: `140deg` Learning source thumbs; `150deg` Brief portraits, Swarm viewports, Report tiles/avatars; `160deg` Learning site-map screenshot.

### 0.3 Body background (per frame; ellipse differs slightly)
```css
html, body { margin: 0; padding: 0; }
body {
  background-color: #FAF7F2;
  background-image:
    radial-gradient(ellipse <W> <H> at 50% <Y>, #FAF7F2 0%, rgba(250,247,242,<A>) <S>, rgba(250,247,242,0) 80%),
    url("assets/dot-field.png");
  background-repeat: no-repeat, no-repeat; background-position: center <P>, center top;
  background-size: auto, 100% auto; background-attachment: fixed, fixed;
}
a { color: #FF5A1F; text-decoration: none; } a:hover { color: #141414; }
```
| Frame | ellipse | A / S | P |
|---|---|---|---|
| Input | `62% 46% at 50% 58%` | `0.88` / `45%` (fade ends `78%`) | `56%` |
| Top Bar | `70% 40% at 50% 60%` | `0.85` / `50%` | `55%` |
| Learning A/B | `70% 50% at 50% 62%` | `0.9` / `48%` | `58%` |
| Brief | `72% 46% at 50% 60%` | `0.9` / `48%` | `56%` |
| Swarm A/B | `72% 46% at 50% 58%` | `0.9` / `48%` | `56%` |
| Report | `74% 48% at 50% 58%` | `0.9` / `48%` | `56%` |

### 0.4 `<pre>` ASCII styling (seven variants)
All: `margin: 0; font-family: 'Geist Mono', ui-monospace, monospace; white-space: pre;` plus:
| # | Where | font-size / line-height / color / padding | grid |
|---|---|---|---|
| P1 | Learning source thumb (read cards) | 7px / 7px / `rgba(20,20,20,0.45)` / 5px | 28×8 (doubled glyphs) |
| P2 | Learning source thumb (unread) | 7px / 7px / `rgba(20,20,20,0.4)` / 5px | 28×8 |
| P3 | Learning site-map screenshot | 7px / 8.6px / `rgba(20,20,20,0.42)` / 8px, `letter-spacing: 0.02em` | 110×30 |
| P4 | Brief persona portrait | 8px / 8px / `rgba(20,20,20,0.5)` / 8px | 23–24×10 |
| P5 | Swarm viewport | 7px / 8px / `rgba(20,20,20,0.44)` / 6px | 60×28 |
| P6 | Report evidence + replay tiles | 7px / 8px / `rgba(20,20,20,0.42)` / 6px | 110×13, 110×22 |
| P7 | Report 22×22 avatar | 5px / 5px / `rgba(20,20,20,0.5)` / 0 | 6×4 |
Ramp (dark→light): `@ 8 0 G C L f t 1 i ; : , . <space>`. Learning thumbs double every glyph (`@@ 88 00 …`) so cells read square at 7px. Portraits are a radial "head" shape padded with `:` rather than spaces; the avatar is exactly `" ;tt; " / ";fCCf;" / "1LGGL1" / "fCG0GC"`.

### 0.5 Keyframes (verbatim; note two different irisScan ranges)
```css
@keyframes irisScan { 0% { top: 4%; } 100% { top: 94%; } }     /* Learning */
@keyframes irisScan { 0% { top: 2%; } 100% { top: 96%; } }     /* Swarm */
@keyframes irisPulse { 0%, 100% { opacity: 1; } 50% { opacity: 0.35; } }
@keyframes irisBlip { 0%, 100% { transform: scale(1); opacity: 1; } 50% { transform: scale(1.35); opacity: 0.6; } }
```
Report declares none. B frames declare irisScan but never apply it (their scan-lines are frozen).

### 0.6 Top bar (identical in all screens; only chip states change)
```
div  position: sticky; top: 0; z-index: 5; backdrop-filter: blur(2px); border-bottom: 1px solid rgba(20,20,20,0.1);
└── div  display: grid; grid-template-columns: auto 1fr auto; align-items: center; gap: 20px; padding: 0 28px; min-height: 64px;
    ├── logo   display: flex; align-items: center; gap: 10px;
    │   ├── BracketMark  position: relative; width: 12px; height: 12px; display: block; flex-shrink: 0;
    │   │     4 corner spans: position:absolute; width:4px; height:4px; border-{top|bottom}:1.5px solid #FF5A1F; border-{left|right}:1.5px solid #FF5A1F
    │   └── span  font-family: 'Instrument Serif', Georgia, serif; font-size: 30px; line-height: 1;   → "Iris"
    ├── stages display: flex; align-items: center; justify-content: center; flex-wrap: nowrap; gap: 2px; min-width: 0; overflow: hidden;
    │          font-family: 'Geist Mono', ui-monospace, monospace; font-size: 11px; font-weight: 500; letter-spacing: 0.1em;
    └── right  display: flex; align-items: center; justify-content: flex-end; flex-wrap: nowrap; gap: 10px; flex-shrink: 0;
        └── counter  font-size: 12px; font-weight: 500; letter-spacing: 0.12em; color: #141414; border: 1px solid rgba(20,20,20,0.18); padding: 6px 10px; white-space: nowrap;  → "[ 8 SESSIONS ]"
```
Stage chips:
```html
<!-- DONE --> <span style="display:flex;align-items:center;gap:5px;color:#141414;padding:6px 6px;white-space:nowrap;flex-shrink:0;"><span style="color:#1F9D55;font-size:11px;">✓</span>LEARN</span>
<!-- CURRENT --> <span style="display:flex;align-items:center;gap:6px;color:#FF5A1F;background:rgba(255,90,31,0.08);padding:6px 9px;white-space:nowrap;flex-shrink:0;"><span style="width:5px;height:5px;background:#FF5A1F;border-radius:50%;display:block;animation:irisPulse 1.4s ease-in-out infinite;"></span>SWARM</span>
<!-- CURRENT, dotless (Report only) --> <span style="color:#FF5A1F;background:rgba(255,90,31,0.08);padding:6px 9px;white-space:nowrap;flex-shrink:0;">REPORT</span>
<!-- UPCOMING --> <span style="color:#8A8580;padding:6px 6px;white-space:nowrap;flex-shrink:0;">BRIEF</span>
<!-- DIVIDER --> <span style="color:rgba(20,20,20,0.22);">·</span>
```
`[ CACHED ]` pill (Top Bar variant 1b, right slot gap 8px): `font-size: 11px; letter-spacing: 0.12em; color: #8A8580; background: rgba(20,20,20,0.04); border-radius: 999px; padding: 6px 12px; white-space: nowrap;`
Stage order `LEARN · BRIEF · SWARM · FINDINGS · REPORT`. Per frame: Learning = LEARN current; Brief = LEARN ✓, BRIEF current; Swarm = LEARN ✓ BRIEF ✓ SWARM current; Report = four ✓, REPORT current-dotless. FINDINGS is never current in any export.

### 0.7 Main column shell
```
div  min-height: 100vh; display: flex; flex-direction: column; font-family: Inter, system-ui, sans-serif; color: #141414;
└── main  flex: 1; display: flex; flex-direction: column; gap: <G>; padding: <P>; max-width: 1400px; width: 100%; box-sizing: border-box; margin: 0 auto;
```
| Frame | G | P |
|---|---|---|
| Learning | 40px | 44px 32px 64px |
| Brief | 44px | 44px 32px 72px |
| Swarm | 24px | 32px 32px 40px |
| Report | 44px | 48px 32px 72px |

H1 (all screens): `font-family: 'Instrument Serif', Georgia, serif; font-weight: 400; font-size: clamp(38px, 4.6vw, 68px); line-height: 0.98; letter-spacing: -0.015em; margin: 0;` + `max-width: 900px` (Learning, Brief, Report), `text-wrap: balance` (Learning). Texts: "Learning your customers and your site." · "Here's who we'll send." · "Watch them try." · "What broke, for whom, and why."

Common text roles:
| Role | Style |
|---|---|
| SectionLabel (`[ RESEARCH ]`, `[ SITE MAP ]`, `STRESS TESTS`) | mono 11px / 500 / `letter-spacing: 0.18em` / `#8A8580` |
| CountLabel (`14 PIECES OF EVIDENCE · 5 SOURCES`, `12 PAGES · 3 JOURNEYS`, `1 RUN EXCLUDED · TOOLING ERROR`) | mono 11px / `0.14em` / `#8A8580` |
| TallyLabel (Swarm `3 RUNNING · 3 DONE · 1 STALLED · 1 ERROR`) | mono 12px / `0.16em` / `#8A8580` |

---

## 1. Input (`Iris 01 Input.dc.html`)
Hero: `position: relative; flex: 1; min-height: calc(100vh - 64px); display: flex; align-items: center; justify-content: center; padding: 32px 32px 48px; overflow: hidden;`
Stack: `position: relative; z-index: 2; width: 100%; max-width: 660px; display: flex; flex-direction: column; align-items: center; gap: 34px;`
Computer: `<img src="assets/computer-globe-monitor.png" style="position: absolute; left: 50%; bottom: calc(100% + 14px); transform: translateX(-50%); height: min(150px, 26vh); width: auto; max-width: 100%; opacity: 0.2; image-rendering: pixelated; pointer-events: none;">` (sits above the headline).
H1: `font-size: clamp(40px, 6vw, 76px); line-height: 0.96; text-align: center; text-wrap: balance;` → "Send your customers in first."
Form: `width: 100%; max-width: 580px; display: flex; flex-wrap: wrap; gap: 10px;`
Input: `flex: 1 1 300px; min-width: 0; font-family: mono; font-size: 16px; color: #141414; background: #FFFFFF; border: 1px solid rgba(20,20,20,0.22); padding: 15px 18px; outline: none;` focus: `border-color: #FF5A1F; box-shadow: 0 0 0 3px rgba(255,90,31,0.12);` placeholder `https://northwindoutfitters.com`.
Button: `font-family: mono; font-size: 13px; font-weight: 500; letter-spacing: 0.14em; color: #FFFFFF; background: #FF5A1F; border: none; padding: 15px 28px; white-space: nowrap;` hover `#E44B12`, active `translateY(1px)` → "RUN IRIS →". Counter in this frame reads `[ 0 SESSIONS ]`.

---

## 2. Learning (`Iris 02 Learning.dc.html`)
Two columns: `display: grid; grid-template-columns: repeat(auto-fit, minmax(340px, 1fr)); gap: 48px; align-items: start;` Each column `display: flex; flex-direction: column; gap: 16px; min-width: 0;`.

**Source grid:** `display: grid; grid-template-columns: repeat(3, minmax(0, 1fr)); gap: 14px;`
**SourceCard:** shell `display: flex; flex-direction: column; gap: 7px; min-width: 0;` (+ `position: relative` when focused). Thumb `aspect-ratio: 4 / 3; background: linear-gradient(140deg, C1, C2); border: 1px solid rgba(20,20,20,0.12); overflow: hidden;`. Caption `mono 10px; letter-spacing: 0.08em; line-height: 1.4; color: #141414` (focused: `#FF5A1F`).
**FocusBracket (Learning):** `position: absolute; inset: 5px; pointer-events: none;` with four 11px corners, `2px solid #FF5A1F`.
**QuoteStrip:** `display: flex; gap: 6px; background: rgba(255,90,31,0.1); padding: 6px 7px;` → marker `mono 9px #FF5A1F` ">" + text `mono 9px; line-height: 1.45; #141414`.
Cards (order, gradient, caption): 1 `#FFD9CF→#F3E9D2` TRUSTPILOT · 2 `#E5DDF5→#D8ECE3` GOOGLE REVIEWS · 3 `#D8ECE3→#FFD9CF` REDDIT r/OUTDOORS (focused in A) · 4 `#F3E9D2→#E5DDF5` APP STORE · 5 `#D8ECE3→#E5DDF5` HELP CENTRE · 6 `#FFD9CF→#E5DDF5` COMPETITOR: ARC'TERYX · 7 `#F3E9D2→#D8ECE3` YOUTUBE REVIEWS · 8 `#E5DDF5→#FFD9CF` SUPPORT TICKETS · 9 `#D8ECE3→#F3E9D2` INSTAGRAM COMMENTS. A: cards 1–3 have quote strips ("checkout resets on my phone every time", "sizing chart is buried three clicks deep", "nobody says which shell is actually waterproof"); count `14 PIECES OF EVIDENCE · 5 SOURCES`.

**Site map column:** `display: grid; grid-template-columns: repeat(auto-fit, minmax(240px, 1fr)); gap: 16px; align-items: stretch;`
**BrowserPanel:** `border: 1px solid rgba(20,20,20,0.14); background: #FAF7F2; display: flex; flex-direction: column;` chrome `display: flex; align-items: center; gap: 8px; padding: 8px 10px; border-bottom: 1px solid rgba(20,20,20,0.12);` with three 6px squares `rgba(20,20,20,0.22)` and URL `mono 9px; letter-spacing: 0.06em; #8A8580; ellipsis`. Viewport `position: relative; flex: 1; min-height: 210px; background: linear-gradient(160deg, #F3E9D2, #FFD9CF); overflow: hidden;` + ScanLine `position: absolute; left: 0; right: 0; height: 2px; background: #FF5A1F; box-shadow: 0 0 10px rgba(255,90,31,0.55); animation: irisScan 2.8s linear infinite;` (B: static at `top: 74%`).
**SiteMapGraph:** container `position: relative; min-height: 250px; padding: 8px; box-sizing: border-box; border: 1px solid rgba(20,20,20,0.1);` SVG `viewBox="0 0 100 100" preserveAspectRatio="none"` absolute-filled; edges are cubic Béziers, e.g. `M 10 50 C 24 50, 26 26, 42 26` (journey edge: `stroke="#FF5A1F" stroke-width="0.45" opacity="0.9"`; plain edge: `stroke="#141414" stroke-width="0.35" opacity="0.5"`, B's new edges `opacity="0.4"`).
**SiteMapNode:** default `position: absolute; transform: translate(-50%, -50%); display: flex; align-items: center; gap: 7px; mono 10px; color: #141414; background: #FAF7F2; border: 1px solid rgba(20,20,20,0.2); padding: 4px 7px; white-space: nowrap;`; journey variant `color: #FF5A1F; border: 1px solid #FF5A1F;` with tag `font-size: 8px; letter-spacing: 0.1em; color: #FF5A1F; opacity: 0.85;` → `JOURNEY 1`.
Node positions A: `/` (10%,50%) · `/collections/jackets` (46%,26%) J1 · `/products/alpine-shell` (46%,74%) · `/cart` right 2% top 30% J2 · `/checkout` right 2% top 70% J3. Count `12 PAGES · 3 JOURNEYS`.

**B diff:** focus bracket moves card 3 → card 4 (caption colours swap); cards 4 and 5 gain quote strips ("delivery estimate changes at checkout", "CAD pricing is not shown until payment"); count → `19 PIECES OF EVIDENCE · 6 SOURCES`; scan-line frozen at 74%; graph gains `/collections/pants` (44%,8%) and `/pages/shipping` (42%,92%) with edges `M 10 50 C 22 50, 24 8, 40 8` and `M 10 50 C 22 50, 24 92, 38 92`; count → `14 PAGES · 3 JOURNEYS`.

---

## 3. Brief (`Iris 03 Brief.dc.html`)
Map block: `position: relative; width: fit-content; max-width: 100%; margin: 0 auto;` with `<img src="assets/world-dots.png" style="display: block; height: 33vh; width: auto; max-width: 100%; opacity: 0.9;">`.
**MapBlip** ×8: wrapper `position: absolute; left: X; top: Y; transform: translate(-50%, -50%); display: flex; flex-direction: column; align-items: center; gap: 3px;`; dot `width: 9px; height: 9px; background: #FF5A1F; border-radius: 50%; animation: irisBlip 2s ease-in-out <delay> infinite;`; label `mono 9px; letter-spacing: 0.1em; #FF5A1F`.
| left | top | label | delay | label position |
|---|---|---|---|---|
| 16% | 27.6% | US | 0 | below |
| 22.9% | 33.1% | US | 0.3s | below |
| 25.7% | 24.5% | US | 0.6s | below |
| 29.4% | 25.4% | US | 0.9s | below |
| 15.8% | 19% | CA | 0.15s | above |
| 27.9% | 23.2% | CA | 0.45s | above |
| 50% | 17.4% | GB | 0.75s | above |
| 53.7% | 16.7% | DE | 1.05s | below |

Persona grid: `display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 16px; align-items: stretch; grid-auto-rows: 1fr;`
**PersonaCard:** `display: flex; flex-direction: column; gap: 10px; border: 1px solid rgba(20,20,20,0.14); background: #FAF7F2; padding: 12px; min-width: 0;` (pair cards: `border: 1px solid #FF5A1F`). Portrait `background: linear-gradient(150deg, C1, C2); border: 1px solid rgba(20,20,20,0.08); overflow: hidden;` (P4 pre). Name `font-size: 20px; line-height: 1.2; letter-spacing: -0.01em;`. ChipRow `display: flex; flex-wrap: wrap; gap: 5px;`. **Chip (Brief):** `mono 9px; letter-spacing: 0.1em; color: #141414; border: 1px solid rgba(20,20,20,0.18); padding: 3px 6px;` accented (the differing chip of the pair): `color: #FF5A1F; border: 1px solid #FF5A1F;`. Task `font-size: 13px; line-height: 1.5;`. **EvidenceQuote:** `background: rgba(20,20,20,0.04); padding: 8px; display: flex; flex-direction: column; gap: 4px;` → quote `mono 9px; line-height: 1.5; #141414` + attribution `mono 9px; letter-spacing: 0.06em; #8A8580` ("— Trustpilot, Jun 2026").
Pair wrapper: `position: relative; grid-column: span 2; display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 16px;` with **PairTick** `position: absolute; left: 50%; top: 58px; transform: translateX(-50%); width: 40px; height: 1px; background: #FF5A1F;` and **PairLabel** `position: absolute; left: 50%; top: 66px; transform: translateX(-50%); mono 8px; letter-spacing: 0.12em; color: #FF5A1F; background: #FAF7F2; border: 1px solid #FF5A1F; padding: 3px 6px; white-space: nowrap;` → `MATCHED PAIR · DEVICE`.
Persona gradients in order: `#FFD9CF→#F3E9D2`, `#E5DDF5→#D8ECE3`, `#F3E9D2→#FFD9CF` (×2 pair), `#D8ECE3→#E5DDF5`, `#FFD9CF→#E5DDF5`, `#F3E9D2→#D8ECE3`, `#E5DDF5→#FFD9CF`.
**StressTestTable:** `display: grid; grid-template-columns: minmax(120px, 1fr) minmax(140px, 1.4fr) minmax(90px, 0.8fr); border-top: 1px solid rgba(20,20,20,0.16);` header cells `mono 10px; letter-spacing: 0.14em; #8A8580; padding: 10px 12px; border-bottom: 1px solid rgba(20,20,20,0.1);` (first col `10px 12px 10px 0`, last `10px 0 10px 12px`); body cells `mono 11px; line-height: 1.5; #141414; padding: 11px 12px; border-bottom: 1px solid rgba(20,20,20,0.08);` (col 3 `#8A8580`; last row no border).

---

## 4. Swarm (`Iris 04 Swarm.dc.html`)
Header block `display: flex; flex-direction: column; gap: 14px;` (H1 + TallyLabel). Feed grid (export): `repeat(auto-fit, minmax(200px, 1fr)); gap: 16px; grid-auto-rows: 1fr;` — **app decision: fixed `repeat(4, minmax(0, 1fr))`** so 4×2 fits at 1440.
**FeedCard shells:** running `display: flex; flex-direction: column; gap: 9px; border: 1px solid rgba(20,20,20,0.14); background: #FAF7F2; padding: 12px; min-width: 0;` (+`position: relative` when focused); stalled `border: 1px solid rgba(217,48,37,0.5)`; done `border: 1px solid rgba(31,157,85,0.5)`; error `border: 1px solid rgba(20,20,20,0.12); background: rgba(20,20,20,0.02)`.
Header row `display: flex; align-items: flex-start; justify-content: space-between; gap: 8px;` name `font-size: 14px; line-height: 1.25; letter-spacing: -0.005em;` (error: `#8A8580`).
**StatusPill:** RUNNING `display: flex; align-items: center; gap: 5px; mono 8px; letter-spacing: 0.1em; color: #FF5A1F; border: 1px solid #FF5A1F; padding: 3px 5px;` with 4px pulsing dot; DONE `gap: 4px; color: #1F9D55; border: 1px solid #1F9D55;` → `✓ DONE`; STALLED `color: #D93025; border: 1px solid #D93025;`; ERROR `color: #8A8580; border: 1px solid rgba(20,20,20,0.2);`.
**Chip (Swarm):** `mono 8px; letter-spacing: 0.1em; color: #141414; border: 1px solid rgba(20,20,20,0.18); padding: 2px 5px;` (row gap 4px); muted `color: #8A8580; border-color: rgba(20,20,20,0.14)`.
**ViewportTile:** `flex: none; aspect-ratio: 16 / 10; border: 1px solid rgba(20,20,20,0.12); display: flex; flex-direction: column; overflow: hidden;` (stalled `rgba(217,48,37,0.3)`, done `rgba(31,157,85,0.3)`, error `rgba(20,20,20,0.1)`). Chrome `display: flex; align-items: center; gap: 5px; padding: 5px 7px; border-bottom: 1px solid rgba(20,20,20,0.1);` two 4px squares + URL `mono 8px #8A8580 ellipsis`. Screen `position: relative; flex: 1; background: linear-gradient(150deg, C1, C2); overflow: hidden;` + ScanLine `height: 1px; background: #FF5A1F; box-shadow: 0 0 8px rgba(255,90,31,0.5); animation: irisScan <2.2|2.6|1.9|2.4|2.1>s linear infinite;`.
Overlays: STALLED `position: absolute; inset: 0; background: rgba(217,48,37,0.3); display: flex; align-items: center; justify-content: center;` → `mono 10px / 500 / 0.16em / #FFFFFF` "STALLED"; DONE `background: rgba(31,157,85,0.32)` → `font-size: 44px; color: #FFFFFF` "✓". ERROR screen (no gradient): `flex: 1; background: rgba(20,20,20,0.06); display: flex; align-items: center; justify-content: center; padding: 8px;` → `mono 9px; letter-spacing: 0.12em; #8A8580` "TOOLING ERROR · EXCLUDED".
**NarrationRow:** `display: flex; gap: 5px;` marker `mono 9px` in status colour (`#FF5A1F` running, `#D93025` stalled, `#1F9D55` done, `#8A8580` error) ">" + text `mono 9px; line-height: 1.45; #141414` (error `#8A8580`).
**FocusBracket (Swarm):** `position: absolute; inset: -5px; pointer-events: none;` four 13px corners `2px solid #FF5A1F` (outside the card).
Cards A (persona · status · URL · gradient · narration): 1 First-time mobile shopper, Canada · RUNNING · `…/collections/jackets` · `#FFD9CF→#F3E9D2` · "looking for the cart… the ＋ button has no label… trying again" · 2 Returning gear buyer, US · RUNNING (focused) · `…/products/alpine-shell` · `#E5DDF5→#D8ECE3` · "opened the size guide… chart is an image with no text… scrolling" · 3 Coupon hunter, US (DESKTOP) · RUNNING · `…/checkout` · `#F3E9D2→#FFD9CF` · "typed promo code SPRING20… the field cleared itself… retyping" · 4 Coupon hunter, US (MOBILE) · STALLED · `…/cart` · `#F3E9D2→#FFD9CF` · "overlay keeps intercepting clicks" · 5 Cold-weather researcher, Germany · RUNNING · `…/products/alpine-shell` · `#D8ECE3→#E5DDF5` · "comparing two shells… spec table has no waterproof rating" · 6 Gift buyer, UK · DONE · `…/checkout/confirm` · `#D8ECE3→#F3E9D2` · "reached order confirmation in 4 steps" · 7 Price-sensitive local, Canada · RUNNING · `…/cart` · `#F3E9D2→#D8ECE3` · "switched country to CA… prices still shown in USD" · 8 Club bulk buyer, US · ERROR · `northwindoutfitters.com` · flat · "session ended before the first step". Note "＋" is U+FF0B.
**B diff:** tally `3 RUNNING · 3 DONE · 1 STALLED · 1 ERROR`; card 1 narration "found the jacket… adding to cart"; card 2 "cart shows 1 item… opening checkout" and loses focus; cards 3 and 5 flip to DONE (green pill, viewport border `rgba(31,157,85,0.3)`, URL `…/checkout/confirm`, gradient `#D8ECE3→#F3E9D2`, green overlay, narration "promo code accepted on the third attempt" / "compared both shells and reached the size guide"); card 7 gains focus. App decision: on DONE the card shell border becomes `rgba(31,157,85,0.5)` (the export is inconsistent between cards 3/5 and 6).

---

## 5. Report (`Iris 05 Report.dc.html`)
Score band `display: flex; flex-direction: column; gap: 14px;` → score row `display: grid; grid-template-columns: repeat(auto-fit, minmax(260px, 1fr)); gap: 28px; border-top: 1px solid rgba(20,20,20,0.16); border-bottom: 1px solid rgba(20,20,20,0.16); padding: 26px 0;` + ExclusionNote.
**ScoreBlock:** `display: flex; flex-direction: column; gap: 8px;` numeral `mono; font-size: clamp(72px, 10vw, 132px); line-height: 0.86; letter-spacing: -0.04em;` (`#8A8580` for 85, `#FF5A1F` for 58); caption `mono 11px; line-height: 1.6; letter-spacing: 0.12em;` (`#8A8580` "CLOUDFLARE STATIC SCORE · robots.txt, llms.txt, headers"; `#141414` "IRIS MEASURED · 8 real agents, 3 journeys").
Split: `display: grid; grid-template-columns: minmax(280px, 1fr) minmax(0, 2fr); gap: 40px; align-items: start;`
**FlagList:** `display: flex; flex-direction: column; border-top: 1px solid rgba(20,20,20,0.14);` **FlagRow:** `display: flex; flex-direction: column; gap: 9px; padding: 16px 0; border-bottom: 1px solid rgba(20,20,20,0.1);` selected adds `background: rgba(255,90,31,0.05)`. Inner rows `display: flex; flex-wrap: wrap; align-items: center; gap: 10px|8px; padding: 0 12px;`; title `font-size: 17px; letter-spacing: -0.01em;`; **SeverityTag:** `mono 9px; letter-spacing: 0.1em; padding: 3px 6px;` orange `color: #FF5A1F; background: rgba(255,90,31,0.12)` "FAILS ONLY ON MOBILE" / red `color: #D93025; background: rgba(217,48,37,0.1)` "FAILS FOR EVERYONE"; **Avatar** `width: 22px; height: 22px; background: linear-gradient(150deg, C1, C2); overflow: hidden;` (P7 pre); reach `mono 10px; letter-spacing: 0.1em; #8A8580` "~41% OF SHOPPERS".
Rows: Cookie wall (selected, mobile-only, 3 avatars, 41%) · Icon-only cart button (everyone, 5, 63%) · Geo-blocked pricing (everyone, 2, 18%) · Hidden mobile nav (mobile-only, 3, 29%).
**Detail:** `display: flex; flex-direction: column; gap: 24px;` summary `font-size: 24px; line-height: 1.35; letter-spacing: -0.01em; max-width: 640px; text-wrap: pretty;`; evidence grid `repeat(auto-fit, minmax(260px, 1fr)); gap: 20px; align-items: stretch;`.
**EvidenceCard:** `display: flex; flex-direction: column; gap: 12px; border: 1px solid rgba(20,20,20,0.14); background: #FAF7F2; padding: 14px;` tile `background: linear-gradient(150deg, #FFD9CF, #F3E9D2); border: 1px solid rgba(20,20,20,0.08); height: 84px; overflow: hidden;`; source `mono 10px; 0.1em; #8A8580` "TRUSTPILOT · JUN 2026"; quote `mono 12px; line-height: 1.6; #141414` "\"I tapped OK four times before it took. Gave up and bought elsewhere.\""; link `mono 10px; 0.1em; #FF5A1F` "READ THE REVIEW ↗".
**ReplayCard:** same card shell; browser `border: 1px solid rgba(20,20,20,0.12);` chrome two 5px squares, gap 6px, padding `6px 8px`; screen `position: relative; height: 150px; background: linear-gradient(150deg, #F3E9D2, #FFD9CF); overflow: hidden;`; OK target `position: absolute; left: 46%; top: 58%; width: 34px; height: 20px; border: 1px solid rgba(20,20,20,0.45); background: rgba(250,247,242,0.9); display: flex; align-items: center; justify-content: center; mono 8px; #141414` "OK"; bracket at the same box with `margin: -7px 0 0 -7px; padding: 7px;` and four 9px corners `2px solid #FF5A1F`; caption `mono 10px; 0.12em; #FF5A1F` "STEP 4 · 00:41".
**FixPanel:** `display: flex; flex-direction: column; gap: 14px; border: 1px solid rgba(31,157,85,0.45); background: rgba(31,157,85,0.07); padding: 18px;` label `mono 10px / 500 / 0.16em / #1F9D55` "PROPOSED FIX"; text `font-size: 15px; line-height: 1.6; max-width: 640px; text-wrap: pretty;`; buttons row `display: flex; flex-wrap: wrap; gap: 10px;`; primary `mono 12px / 500 / 0.12em; color: #FFFFFF; background: #FF5A1F; border: none; padding: 13px 22px;` hover `#E44B12` → "OPEN REPLAY ↗"; secondary `color: #141414; background: transparent; border: 1px solid rgba(20,20,20,0.3);` hover `border-color: #141414` → "COPY FIX". Both active `translateY(1px)`.

---

## 6. Known inconsistencies (decided for the app)
1. Swarm A tally text doesn't match its DOM → the app derives the tally from state.
2. Two `irisScan` ranges → keep both (`irisScan` 2–96% for feeds, `irisScanPanel` 4–94% for the Learning panel).
3. DONE card shell border: use `rgba(31,157,85,0.5)` everywhere.
4. Current-chip padding `6px 9px`.
5. Selected FlagRow: the orange wash is the treatment; no left rule.
6. FINDINGS never renders as current in the exports; in the app it is current during the `score` stage, then REPORT on `done`.
