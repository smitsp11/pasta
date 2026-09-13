# Iris — Design brief and Claude Design frame prompts

Companion to `docs/ui-flow.md` (what each screen does and why). This file is *how it looks and moves*, plus one ready-to-paste prompt per frame for Claude Design. Animations are described so they can be coded after the sketches exist; Claude Design only needs to show the resting and mid-motion states.

References (screenshots in `.context/design-refs/` and `.context/attachments/`):
- **God's Eye** (Furious 7, Cantina Creative): the *motion* reference. Clip: youtube.com/watch?v=bTlK6eB4fV0 · breakdown: youtube.com/watch?v=aiaGDpFMTQk
- **Firecrawl**: the *type and palette* reference. Warm off-white, ink type, one orange accent, grid paper, monospace annotations.
- **Firecrawl-style ASCII cards** (attachment 1): images rendered as characters on pastel gradients, serif headlines. The *texture* reference.
- **Browserbase**: the *illustration* reference. Dithered pixel art, highlighter-block headlines. The retro computer graphic (attachment 2).
- **Reducto**: serif display face used sparingly.

---

## 1. Direction in one paragraph

Light, warm, textured, and alive. Firecrawl's paper-and-ink base with a single orange "scan" accent. Every image on the page (a persona, a site screenshot, a replay frame) is rendered as **ASCII texture** or **dithered pixels**, never as a flat photo, so the whole product looks like one machine drawing what it sees. Motion borrows God's Eye's "searching everything" choreography: reticles jumping across feeds, counters ticking, matches lighting up, a pixel-dissolve between stages. Dense texture lives *inside* panels; the page itself stays calm so it reads on a projector.

## 2. System

**Palette**
| Token | Value | Use |
|---|---|---|
| paper | `#FAF7F2` | page background |
| ink | `#141414` | text, lines |
| grid | ink at 6% | grid-paper lines, 24px cell |
| scan | `#FF5A1F` | live / searching / primary action (Firecrawl orange) |
| scan-soft | `#FFE6DA` | ASCII card gradient top, highlights |
| ok | `#1F9D55` | completed |
| stall | `#D93025` | stalled |
| muted | `#8A8580` | tooling errors, metadata |
| pastel set | `#FFD9CF` `#F3E9D2` `#E5DDF5` `#D8ECE3` | ASCII card gradients, one per persona segment |

**Type**
- Display (serif): **Instrument Serif** or Tiempos. The five narrative headlines only, 56–96px.
- UI (sans): **Inter** or Geist. Everything else.
- Mono: **Geist Mono** or JetBrains Mono. Chips, counters, logs, `[ ANNOTATIONS ]`, ASCII textures.

**Textures (all generated in code from a source image; Claude Design just draws the look)**
- **ASCII image**: source image → luminance → character ramp `" .:;i1tfLCG08@"`, 8px mono glyphs, ink on a pastel gradient card. Used for persona portraits, site thumbnails, replay frames.
- **Dither**: source image → Bayer 4×4 ordered dither to a 5-colour palette (paper, ink, scan, ok, pastel). Used for hero illustrations and the "computer" graphic.
- **Grid paper**: 24px cell, 6% ink lines, on every page background.
- **Dot-matrix map**: world map as a dot grid; dots light in `scan` for persona countries.

**Chips (mono, 11px, uppercase)**
`DESKTOP` `MOBILE` · `US` `CA` `DE` · `NEW` `RETURNING` · `DOM` `VISION`

**Motion vocabulary (to code later)**
| Name | What | Where |
|---|---|---|
| reticle | square bracket corners that jump between targets, 120ms hop, brief lock | research feed, swarm feeds, replay |
| scan-line | thin horizontal `scan` line sweeping top→bottom over a live panel, 2.4s loop | any panel that is "looking" |
| tick | numbers count up with mono digits rolling | evidence count, sessions, score |
| pixel-dissolve | Cantina's transition: blocks resolve from noise to image, 600ms | between stages, on card state change |
| wireframe-grow | site map draws itself node by node with connecting lines | screen 2 right |
| light-up | a dot on the map goes from grid-grey to `scan` with a 300ms pulse | persona countries, match markers |

**Persistent frame (every screen)**
Top bar: wordmark `Iris` (serif) · stage bar with five steps `LEARN · BRIEF · SWARM · FINDINGS · REPORT` (mono, current step in `scan`) · right side: `[ 8 SESSIONS ]` counter and a `[ CACHED ]` pill when in fallback mode.
Navigation model: **one vertical page that grows** as stages complete; the stage bar scrolls you. No wizard, no clicking to advance. On stage, the presenter never has to find a button.

**Stage constraints**
Readable from the back of a room: minimum 16px body, 20px in panels, headline ≥56px. No element that only reads at arm's length. The score contrast on screen 5 is the single largest thing on the page.

---

## 3. Frames

Sample data for every frame (use exactly this so frames match): brand **Northwind Outfitters**, a mid-size outdoor-clothing store. Journeys: *find a jacket*, *add it to the cart*, *reach checkout*. Cloudflare static score 85. Iris score 58.

### Frame 1 — Input

Layout: full-viewport hero on grid paper. Centre: serif headline, one wide input, one small optional input, one `scan` button. Behind, at 30% opacity, a dithered illustration of a retro computer whose screen shows a dot-matrix globe (the Browserbase computer, ours). Mono annotations in the corners: `[ READY ]`, `[ 0 SESSIONS ]`, `[ STEEL · CONNECTED ]`.

Copy: headline *"Send your customers in first."* sub *"Paste a URL. We'll learn who your customers are and map your site at the same time."* input placeholder `https://northwindoutfitters.com` · optional `what does the company do? (optional)` · button `Run Iris`.

Motion: globe on the computer screen rotates slowly; on submit, pixel-dissolve into Frame 2.

### Frame 2 — Learning (split screen)

Layout: two equal columns under a serif headline *"Learning your customers and your site."* Each column has a mono label, a live panel, and a running counter.

**Left, `[ RESEARCH ]`**: a 3×3 wall of source cards (Trustpilot, Google Reviews, Reddit, App Store, Help Centre, competitor…). Each card is an ASCII-textured thumbnail of the source page on a pastel gradient with the source name in mono. A **reticle** sits on one card (the one being read); cards already read show a `scan` quote strip underneath: *"checkout resets on my phone every time" — Trustpilot*. Counter: `14 PIECES OF EVIDENCE · 5 SOURCES`.

**Right, `[ SITE MAP ]`**: left half a live Steel viewer (show as a browser frame with an ASCII-textured page inside); right half a **wireframe-grow** graph: nodes labelled `/`, `/collections/jackets`, `/products/alpine-shell`, `/cart`, `/checkout`, lines between them, three nodes highlighted in `scan` as the discovered journeys. Counter: `12 PAGES · 3 JOURNEYS`.

Motion: reticle hops every ~1.5s; scan-line over the Steel viewer; graph nodes appear with pixel-dissolve; both counters tick.

### Frame 3 — Test brief

Layout: serif headline *"Here's who we'll send."* Below, a wide dot-matrix world map (paper dots), with 8 persona countries **lit** in `scan`. Under the map, a 4×2 grid of persona cards. Below the grid, the stress-test list as a mono table.

Persona card (fields, in order): ASCII portrait on the segment's pastel gradient (a generated abstract face or silhouette, not a stock photo) · segment name (sans, 20px) *"First-time mobile shopper, Canada"* · three chips `MOBILE` `CA` `NEW` · goal (sans 16px) *"Find a jacket and add it to the cart."* · evidence quote in a muted box (mono 13px) *"the mobile site keeps resetting my cart" — Trustpilot, Jun 2026*.

Matched pair: cards 3 and 4 identical except `DESKTOP` vs `MOBILE`, joined by a thin `scan` line with a mono label `MATCHED PAIR · DEVICE`.

Stress-test list (mono table): `PROBE` · `WHY` · `SOURCE` rows: *checkout on mobile · 3 reviewers report resets · Trustpilot*, *coupon field · rejects valid codes · Reddit r/…*, *country pricing · CAD not shown · Help centre*.

Motion: map dots light up one by one, then cards pixel-dissolve in left to right.

### Frame 4 — Swarm

Layout: serif headline *"Watch them try."* Header line mono: `6 RUNNING · 1 DONE · 1 STALLED`. A 4×2 wall of live-feed cards, one per persona.

Feed card: persona name + three chips on top · the live Steel viewer (browser frame; in the mock show an ASCII-textured store page) with a **scan-line** while running · bottom: narration line in mono, latest step only: *"looking for the cart… the ＋ button has no label… trying again"* · status pill top-right: `RUNNING` (scan) / `DONE` (ok) / `STALLED` (stall) / `ERROR` (muted).

Show three states in the frame: five running with scan-lines, one done (feed pixel-dissolved to a solid `ok` tint with a ✓), one stalled (solid `stall` tint with the last narration line), one error (muted with `TOOLING ERROR · EXCLUDED`).

Motion: reticle roams the wall, pausing on whichever card just emitted an event; on finish, the feed pixel-dissolves into its status tint.

### Frame 5 — Report

Layout: calm. Serif headline *"What broke, for whom, and why."* Then the contrast block: two huge numbers side by side, mono captions: left `85` muted, caption `CLOUDFLARE STATIC SCORE · robots.txt, llms.txt, headers`; right `58` in `scan`, caption `IRIS MEASURED · 8 real agents, 3 journeys`. Under it, a one-line mono strip: `1 RUN EXCLUDED · TOOLING ERROR`.

Then the flags list (left third) and the flag detail (right two-thirds).

Flag row: category (sans 18px) *Cookie wall* · attribution badge `FAILS ONLY ON MOBILE` (scan-soft bg) or `FAILS FOR EVERYONE` (stall-soft) · `EVERY ENGINE` black pill when engine consensus · affected personas as tiny ASCII portraits · customers-affected count `~41% OF SHOPPERS`.

Flag detail: description (sans 24px) *"A consent overlay covers the page and its OK button is 16px on mobile."* · two columns: left, the customer quote card (ASCII-textured source thumbnail + quote + link); right, the replay frame (browser frame, ASCII-textured, a **reticle** locked on the tiny OK button, mono caption `STEP 4 · 00:41 · sess-mobile-cart`) · below, green fix box: `PROPOSED FIX` *Give the dialog role="dialog" and an aria-label; make the accept button ≥44×44px on mobile.* · buttons `Open replay ↗` `Copy fix`.

Motion: numbers tick up; the first flag opens automatically; reticle on the replay pulses once.

### Frame 0 — Persistent top bar (component)

Wordmark · stage bar (five mono labels, current in `scan`, completed with a ✓, upcoming muted) · `[ 8 SESSIONS ]` · `[ CACHED ]` pill (only in fallback).

---

## 4. Prompts for Claude Design (paste one per frame)

Each prompt assumes the system above is attached or pasted first. Ask for a desktop frame 1440×900 unless noted.

**System prompt to paste before any frame:**
> Design system: warm off-white paper `#FAF7F2` with a 24px grid-paper background at 6% ink; ink `#141414` text; one accent orange `#FF5A1F` used only for "live/searching" and primary actions; pastel gradient cards `#FFD9CF #F3E9D2 #E5DDF5 #D8ECE3`; success `#1F9D55`, stall `#D93025`, muted `#8A8580`. Type: Instrument Serif for headlines (56–96px), Inter for UI, Geist Mono for chips, counters, logs and annotations like `[ READY ]`. All images are rendered as ASCII-character textures (mono glyphs on pastel gradients) or Bayer-dithered pixel art in the palette; never flat photos. Tone: Firecrawl's technical playfulness meets God's Eye's "searching everything" motion. Panels can be dense; the page stays calm and readable from the back of a room. Persistent top bar: serif wordmark "Iris", a five-step mono stage bar LEARN · BRIEF · SWARM · FINDINGS · REPORT with the current step in orange, and a `[ 8 SESSIONS ]` counter on the right.

**Frame 1 prompt:**
> Frame 1, "Input". Full-viewport hero on grid paper. Centred serif headline "Send your customers in first." Sub-line in Inter: "Paste a URL. We'll learn who your customers are and map your site at the same time." One wide input with placeholder https://northwindoutfitters.com, a smaller optional input "what does the company do? (optional)", and an orange button "Run Iris". Behind the form at 30% opacity, a Bayer-dithered illustration of a retro desktop computer (Browserbase style) whose screen shows a dot-matrix globe. Mono annotations in the four corners: [ READY ] [ 0 SESSIONS ] [ STEEL · CONNECTED ] [ v0.1 ]. Stage bar shows LEARN as upcoming.

**Frame 2 prompt:**
> Frame 2, "Learning", stage LEARN active. Serif headline "Learning your customers and your site." Two equal columns. LEFT, mono label [ RESEARCH ]: a 3×3 wall of source cards (Trustpilot, Google Reviews, Reddit r/Outdoors, App Store, Help Centre, Competitor: Arc'teryx, plus three more), each an ASCII-textured thumbnail on a pastel gradient with the source name in mono; a square-bracket reticle sits on the Reddit card; three already-read cards show an orange quote strip underneath, e.g. "checkout resets on my phone every time" — Trustpilot. Counter under the wall in mono: 14 PIECES OF EVIDENCE · 5 SOURCES. RIGHT, mono label [ SITE MAP ]: a browser frame showing a live view of northwindoutfitters.com rendered as ASCII texture with a thin orange scan-line across it, and beside it a node graph drawing itself: nodes /, /collections/jackets, /products/alpine-shell, /cart, /checkout connected by thin ink lines, with three nodes highlighted orange and labelled JOURNEY 1–3. Counter: 12 PAGES · 3 JOURNEYS.

**Frame 3 prompt:**
> Frame 3, "Test brief", stage BRIEF active. Serif headline "Here's who we'll send." A wide dot-matrix world map in paper-grey dots with 8 dots lit orange (US ×4, CA ×2, DE, GB), each with a tiny mono label. Below, a 4×2 grid of persona cards, each: an ASCII-textured abstract portrait on its pastel gradient; segment name in Inter 20px e.g. "First-time mobile shopper, Canada"; three mono chips MOBILE · CA · NEW; goal line "Find a jacket and add it to the cart."; a muted evidence box in mono: "the mobile site keeps resetting my cart" — Trustpilot, Jun 2026. Cards 3 and 4 are identical except DESKTOP vs MOBILE and are joined by a thin orange line labelled MATCHED PAIR · DEVICE. Under the grid, a mono table titled STRESS TESTS with columns PROBE · WHY · SOURCE and three rows (checkout on mobile · 3 reviewers report resets · Trustpilot; coupon field · rejects valid codes · Reddit; country pricing · CAD not shown · Help centre).

**Frame 4 prompt:**
> Frame 4, "Swarm", stage SWARM active. Serif headline "Watch them try." Mono header line: 6 RUNNING · 1 DONE · 1 STALLED. A 4×2 wall of live-feed cards, one per persona: persona name and three chips on top; a browser frame showing the store page as ASCII texture; a status pill top-right; a mono narration line at the bottom showing only the latest step. Show five cards RUNNING (orange pill, thin orange scan-line across the feed, narration like "looking for the cart… the ＋ button has no label… trying again"), one DONE (feed replaced by a solid green tint with a large ✓), one STALLED (solid red tint, narration "overlay keeps intercepting clicks"), one ERROR (muted grey, label TOOLING ERROR · EXCLUDED). A square-bracket reticle sits on one running card.

**Frame 5 prompt:**
> Frame 5, "Report", stage REPORT active. Calm layout. Serif headline "What broke, for whom, and why." Contrast block: two huge mono numbers side by side, left "85" in muted grey with caption CLOUDFLARE STATIC SCORE · robots.txt, llms.txt, headers; right "58" in orange with caption IRIS MEASURED · 8 real agents, 3 journeys. A thin mono strip: 1 RUN EXCLUDED · TOOLING ERROR. Below, left third: a flags list of four rows, each with category (Cookie wall, Icon-only cart button, Geo-blocked pricing, Hidden mobile nav), an attribution badge (FAILS ONLY ON MOBILE in soft orange, or FAILS FOR EVERYONE in soft red), an optional black pill EVERY ENGINE, a row of tiny ASCII portraits for affected personas, and a customers-affected label like ~41% OF SHOPPERS. Right two-thirds, the first flag open: description in Inter 24px "A consent overlay covers the page and its OK button is 16px on mobile."; two columns: left a customer quote card (ASCII-textured Trustpilot thumbnail, the quote, a link), right a replay frame (browser frame, ASCII-textured store page, an orange reticle locked on a tiny OK button, mono caption STEP 4 · 00:41 · sess-mobile-cart); below, a green box PROPOSED FIX: "Give the dialog role=\"dialog\" and an aria-label; make the accept button at least 44×44px on mobile." and two buttons "Open replay ↗" and "Copy fix".

**Component prompt (top bar):**
> A persistent top bar on paper: serif wordmark "Iris" left; centre, five mono steps LEARN · BRIEF · SWARM · FINDINGS · REPORT where completed steps have a small ✓, the current step is orange, upcoming steps are muted; right, a mono counter [ 8 SESSIONS ] and, in one variant, an additional muted pill [ CACHED ].

---

## 5. Animation choreography (for coding after sketches)

Modelled on the God's Eye scene: the system visibly searches, locks, and confirms.

1. **Submit** → pixel-dissolve from Frame 1 to Frame 2 (600ms). Stage bar: LEARN turns orange.
2. **Research** (Frame 2 left): source cards pixel-dissolve in one by one (150ms apart). Reticle hops to each new card as it is read (120ms hop, 400ms lock). When a quote is found, the quote strip slides up under the card and the evidence counter ticks.
3. **Site map** (Frame 2 right): scan-line loops over the viewer. Each discovered page adds a node with a 200ms pixel-dissolve and a line drawn from its parent (300ms). Journey nodes pulse orange once when chosen.
4. **Brief** (Frame 3): map dots light up sequentially (300ms pulse each), then cards dissolve in left→right (100ms apart). The matched-pair line draws last.
5. **Swarm** (Frame 4): all eight viewers mount with a scan-line. Reticle roams to whichever card just emitted an event. On completion the feed pixel-dissolves to its status tint; the header counters tick.
6. **Report** (Frame 5): the two numbers tick up over 1.2s, the right one last. First flag opens automatically; the replay reticle pulses once and holds.
7. **Fallback**: identical choreography, driven by a recorded run; the `[ CACHED ]` pill is the only difference.

## 6. Asset recipes (code, not design)

- **ASCII from image**: canvas → downsample to (w/8 × h/16) → per cell luminance → index into ramp `" .:;i1tfLCG08@"` → render mono glyphs at 8×16px in ink over a pastel gradient. One function, used for persona portraits, source thumbnails, viewer stills, replay frames.
- **Dither**: canvas → Bayer 4×4 threshold matrix → snap each pixel to the nearest of 5 palette colours. Used for the hero computer and any illustration.
- **Reticle / scan-line**: pure CSS on a positioned overlay; the reticle is four 12px corner brackets animated with `transform` between target rects.
- **Pixel-dissolve**: a canvas noise mask that resolves block by block (16px blocks, 600ms, ease-out).
- **Dot-matrix map**: a static SVG of world dots (equirectangular), with a `data-country` attribute per dot cluster to light up.
