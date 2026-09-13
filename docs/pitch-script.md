# Iris — demo script, Zara & IKEA (3:00)

Every quote, category, and score below is taken from the demo data the front end plays
(`web/src/data/targets/zara.json`, `ikea.json`). If the data changes, change the line.

**Setup before walking on.** Tab 1: `https://iris-tau-two.vercel.app/?target=zara&speed=2`. Tab 2: same URL with
`target=ikea&stage=score` (lands directly on IKEA's report for the cutaway). Full screen, browser zoom 125%.
Rehearse at `speed=2`; the show runs about 45 s of screen time, so the voice sets the pace, not the animation.

Spoken text is ~400 words. Roles: **VO** talks, **Driver** types and clicks. One person can do both.

---

## 0:00–0:15 — The problem

▎ **VO:** "Companies pay forty thousand dollars and wait six weeks for a usability study to learn how customers
behave on their site. Most skip it, ship, and read the complaints later. And the customer is changing: AI
agents are now a fifth of some stores' traffic, and nobody can tell you if one can reach checkout."

▎ **ON-SCREEN:** Split title card: Zara and IKEA logos with their URLs. Cut to the empty Input screen with the
headline "Send your customers in first."

## 0:15–0:30 — The angle

▎ **VO:** "Iris automates the study. It learns who your real customers are, turns them into eight AI personas,
and sends them through your live site on real cloud browsers, before you deploy. You get the frame where each
one gave up, the customer quote that predicted it, and the fix."

▎ **ON-SCREEN:** Driver types `zara.com`, hits Run. Under the button: "We'll research your customers and map your
site at the same time." Pixel-dissolve into Learning.

## 0:30–0:55 — Screen 2: Learning (split screen)

▎ **VO:** "Two things happen at once. One agent digs up what real Zara customers complain about: Trustpilot,
Mumsnet, Reddit, a UX audit. 'Why is it so hard to shop on Zara's website?' 'Why use a plus symbol for sizes?
It looks like Add to Cart.' The other agent maps the site itself: what you can actually do here."

▎ **ON-SCREEN:** Left: evidence cards landing from nine sources. Point at the Threads card ("why is it so hard to
shop on the zara's website? their layout is so confusing!") and the UX audit card ("Why use the + symbol to
indicate available sizes? It is not clear and appears more like an Add to Cart."). Right: the crawler clicking
through; journey cards appear: **Find a jacket and pick a size**, **Search for a linen blazer**, **Reach checkout**.

## 0:55–1:15 — Screen 3: Test brief

▎ **VO:** "That becomes eight test personas: real segments, on the devices and countries those customers actually
use. A first-time mobile browser in the US. A cross-border shopper in Germany. Two of them are identical except
one thing, so we can prove exactly what broke it."

▎ **ON-SCREEN:** Eight persona cards. Camera holds on the matched pair, p3 and p4: *Returning shopper re-finding an
item, United Kingdom*, desktop, returning, one driven by a DOM agent and one by a vision agent. Evidence quote
underneath: **"God forbid you see something you like and don't buy it there and then, because I can never find
an item if I try looking for it again."** (Mumsnet)

## 1:15–1:50 — Screen 4: The swarm

▎ **VO:** "Now all eight run at once, on real cloud browsers, live. This one is a real mobile device. This one
arrives from a residential IP in Germany. This one is a returning visitor carrying last visit's cookies."

▎ **ON-SCREEN:** Grid of eight live viewers with narration scrolling: "three dialogs on first paint… closed the
privacy popup… a grey backdrop still covers the page", "results loaded… every tile has an unlabelled button
called Open size selector". Driver points at a MOBILE chip, a DE chip, a RETURNING chip. Hold until a card flips
red.

▎ **VO (as the Germany card fails):** "That one just got stuck. It closed the geolocation popup and the page is
still covered."

▎ **VO (as the US desktop card fails):** "And that one picked a size, went to the bag, and the bag is empty."

## 1:50–2:20 — Screen 5: Report (Zara)

▎ **VO:** "Here's why. Picking a size fires an add-to-cart request that Zara's bot gate silently rejects. No error,
the bag stays empty, and no one can reach checkout. Both kinds of agent hit it, so it's the site, not the bot.
And it isn't just us: a real customer said the exact same thing."

▎ **ON-SCREEN:** Score lands: **47 / 100**. Driver clicks the top flag, *Add to bag fails silently*, 62% of
personas affected. Left: the quote **"Had a whole bunch of items in my basket for my holiday and on checkout,
half are gone!!"** Right: replay frozen at step 3, "YOUR BAG IS EMPTY". Green box: *Surface the 403 as a visible
error on the add-to-cart button instead of failing silently.*

▎ **VO (optional, if ahead of time):** "Second flag: every product tile's only button is an unlabelled plus. The
DOM agent stalled, the vision agent got through. That's the matched pair. Fails only for one kind of agent."

## 2:20–2:45 — IKEA cutaway (not a one-site trick)

▎ **VO:** "Same tool, completely different site, no changes. IKEA Canada: sixty-one. Its top flag: the product page
has two Add to cart buttons, and the first one adds a four-hundred-and-ninety-nine-dollar mattress instead of the
bed frame. Every agent hit it."

▎ **ON-SCREEN:** Switch to tab 2. Speed-ramp through Learning and Swarm (2 to 3 s each), land on IKEA's report.
Scores side by side: **Zara 47 / 100 · IKEA 61 / 100**. Driver clicks IKEA's top flag: quote *"I entered my
quantity of 2, continued but noted my quantity had reverted to one"*, replay at the cart showing ÅKREHAMN
mattress $499.00, fix *"name each Add to cart button after its product."*

## 2:45–3:00 — Close

▎ **VO:** "One tool, any site, real customers, real proof, in minutes instead of six weeks. Built on Steel: real
mobile devices, real geo proxies, real returning identities, and the replay of every failure. Point it at yours."

▎ **ON-SCREEN:** Both score cards together, Iris wordmark, `iris-tau-two.vercel.app`. Driver scrolls to the Input
field for the encore.

---

## If something breaks

| Symptom | Do | Say |
|---|---|---|
| Stuck on Input | Reload tab 1 with `&stage=run` | "Let me jump straight to the swarm." |
| Grey swarm cards | Keep narrating; report still lands | "Grey is our tooling, not the site; excluded from the score." |
| No report | Reload with `target=zara&stage=score` | "Here's the report from this morning's run." |
| Running long | Drop the optional second-flag line and the IKEA flag click | Go straight from IKEA's score to Close |

## Do not say

- "Simulated users." The personas come from real quotes and the agents are real browsers doing real tasks.
- "Cloudflare says 85." Zara has no static score in the data; IKEA's is 20. Use "static checkers score
  robots.txt; we score the checkout" if asked.
- "Crucible." The product is Iris.
