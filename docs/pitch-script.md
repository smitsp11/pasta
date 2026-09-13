# Iris — 3-minute pitch script

Built from `README.md`, `docs/ui-flow.md`, and the IKEA Canada demo data the front end actually plays
(`web/src/data/targets/ikea.json`). Every number spoken below is on screen at that moment. If the demo data
changes, change the line.

Spoken text is about 470 words, which is 3:00 at a brisk pace and 3:10 at a calm one; the fallback table says what to cut. Two presenters: **Pitch** (talks) and
**Driver** (types, scrolls, clicks). One presenter can do both; the stage bar scrolls for you.

Before walking on: open `https://iris-tau-two.vercel.app/?target=ikea&speed=2` in a fresh tab, full screen,
browser zoom at 125%. Have the same URL with `&stage=run` in a second tab as the fallback.

---

## 0:00 — Hook (20 s) · Screen: Input, nothing typed yet

> AI-referred traffic to US retail sites grew almost four hundred percent last quarter. Those visitors are
> agents, and they now convert better than humans. Yet no site owner can answer one question: **when an
> agent tries to check out on my site, does it make it?** Today the answer is a usability study. Forty
> thousand dollars, six weeks, five humans.

**Driver:** hands off the keyboard. Let the headline "Send your customers in first." sit on screen.

## 0:20 — The idea (15 s) · Screen: Input

> Iris sends your customers in first. Give it a URL, nothing else. It learns who your real customers are,
> sends eight of them through your live site as agents on real cloud browsers, and shows you the frame
> where each one gave up.

**Driver:** type `ikea.ca`, press Run. Pixel-dissolve into Learning.

## 0:35 — Learning (20 s) · Screen: split screen, both halves live

> Two things at once. Left: a research agent reads IKEA's help centre, Trustpilot, and the app store, and
> pulls real customer quotes. Right: a crawler maps the site. Beds, the MALM bed frame, the cart, the
> checkout. We told it nothing.

**Driver:** as the evidence counter ticks, point at one quote card. As the site map draws, point at the
checkout node.

## 0:55 — Test brief (20 s) · Screen: eight persona cards

> Evidence plus map becomes a test brief: eight personas, each backed by a quote. A first-time mobile
> shopper in Canada. A returning IKEA Family member. A comparison shopper in Germany. Two are a matched
> pair, identical except for one variable, so we can prove a failure is caused by the country, not luck.

**Driver:** hover the linked pair (p3 and p4, Iqaluit, Canada vs Great Britain). Then scroll to the swarm.

## 1:15 — Swarm (30 s) · Screen: grid of eight live Steel viewers

> The swarm: eight Steel sessions at once. This one is a real mobile device, not a spoofed user agent. This
> one arrives from a residential IP in Germany. This one is a returning visitor with a persistent profile,
> carrying the cookies of someone who has been here before. Half are DOM agents, half are vision agents.
>
> Watch the captions. That one tried to add the bed frame. It just added a four-hundred-dollar mattress.

**Driver:** point at a MOBILE chip, a DE chip, a RETURNING chip, a VISION chip as each is named. When cards
turn red, point at the first stalled one. Let the header reach "done".

## 1:45 — Report (35 s) · Screen: score, ranked flags

> Readiness: sixty-one. Static checkers score robots.txt. We score the checkout.
>
> Three flags, ranked by customers affected. Number one: two Add to cart buttons, and the first adds the
> wrong product. Every kind of agent hit it, so it is the site, not the bot. Here is the customer quote
> that predicted it, the replay frozen on the click, and the fix: name the button.
>
> Number three is the matched pair: an unserved Canadian postal code accepted silently. Fails only from
> Canada.

**Driver:** click flag one. Point left at the quote, right at the replay, down at the green fix box. Click
flag three. Point at the "fails only from" attribution line.

## 2:20 — Why this is real, and why Steel (20 s) · Screen: stay on the report

> Three things here cannot be faked from a laptop: a real mobile fingerprint, a residential IP in another
> country, and a browser identity that remembers. Those are Steel primitives, and they are what makes every
> failure attributable. Tooling failures are excluded from the score. No agent ever submits a payment.

## 2:40 — Business (12 s)

> One run replaces a forty-thousand-dollar study for the price of eight browser sessions, so you run it on
> every deploy. Agentic commerce is heading to three to five trillion dollars by 2030. Every one of those
> sites needs to know if the agent makes it to checkout.

## 2:52 — Close (8 s)

> We are Iris. Send your customers in first. And if any judge wants to see their own site, give us the URL.

**Driver:** scroll back to the top so the input field is visible for the encore.

---

## If something breaks

| Symptom | Do this | Say this |
|---|---|---|
| Page is blank or stuck on Input | Switch to the second tab (`&stage=run`) | "Let me jump straight to the swarm." |
| Swarm viewers show grey cards | Keep talking through the captions; the report still lands | "Grey means our tooling, not the site; those are excluded from the score." |
| Report never appears | Reload with `?target=ikea&stage=score` | "Here is the report from the run we did this morning." |
| Projector too dim to read chips | Skip pointing at chips, name them verbally | (no change to script) |
| Running long at the report | Cut flag three, go straight to Business | (drop the matched-pair paragraph) |

The player is deterministic. `speed=2` runs the whole show in roughly 45 seconds of screen time, which
leaves the talk in control of the pace. Rehearse at `speed=2`, not `speed=1`.

## Likely judge questions

**"Was that a real run or a recording?"**
The stage demo is a recorded run replayed through the real front end, because a live run needs a paid proxy
balance and takes about six minutes. The backend runs live: this morning it ran Browser Use and Claude
computer use on real Steel sessions, including mobile mode and a persistent profile handoff, and every
session was released. Offer to run a single live baseline session on a judge's site from the terminal.

**"How is this different from Cloudflare's agent-readiness score or Agent Checker?"**
Cloudflare checks robots.txt, llms.txt, and headers; it never runs an agent. Agent Checker runs one agent,
one way, through fixed tasks. Iris runs a controlled population: every variant differs from baseline in one
variable, so a stall is attributed to device, country, identity, engine, or the site. Nobody else can say
"fails only on mobile" with evidence.

**"How do you know the finding is the site's fault and not your agent's?"**
Two engines with different architectures. A stall that hits both is flagged as engine consensus. Tooling
failures are harness errors, excluded from the score, and retried once. A finding is only reported if an
agent actually reproduced it; research supplies what to test, never the answer.

**"Is it safe to point at a real site?"**
The crawler is read-only: it follows links, never submits forms, never clicks buy, delete, or cancel. The
agents stop at the payment step. A payment guard in the runner ends the run as soon as a payment URL or a
"Place order" button appears.

**"What does a run cost?"**
Eight Steel sessions of about three minutes each, plus roughly twelve to twenty dollars in model calls on
Opus, or a third of that on Sonnet. Against forty thousand dollars and six weeks for the study it replaces.

**"What's next?"**
The fix loop: a Steel Computer clones the store, applies the proposed fix, restarts it, and re-runs the
failing persona so the score climbs live. Then Iris on every deploy as a CI check.

## Do not say

- "Simulated users" or "synthetic customers." The agents are the population, not a stand-in for humans.
- "Hallucinated" anything. Every flag has a replay.
- The static score contrast as "they say 85, we say 58." On the IKEA data the static score is 20; use the
  line "they score robots.txt, we score the checkout" instead.
- "Crucible." The product is Iris.
