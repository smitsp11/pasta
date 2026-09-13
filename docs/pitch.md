# Iris — hackathon pitch (YC-application style)

Track: Steel.dev **Agents on the web**. The track brief lists "a web QA agent that walks through a site and reports
broken forms or confusing states" as a starting direction. Iris is that, taken to its conclusion: the QA agents are
your actual customers, reconstructed from evidence, running on Steel's cloud browsers.

Sections marked **[pick one]** offer options; the first is the recommendation.

---

## Tagline [pick one]

1. **Iris. Send your customers in first.** *Web QA reinvented with Steel web agents.*
2. **Iris: the $40,000 usability study, on every deploy.** Powered by Steel.
3. **Iris reinvents web QA.** Your real customers, as AI agents, on real browsers. Built on Steel.
4. **Your next customer is an agent. Iris finds out if it makes it to checkout.** Built on Steel.

Option 1 is the product name plus the promise, and it survives being said out loud. Option 4 is the sharpest for
Steel's judges because it names the thesis of the track.

---

## The problem

Companies find out how customers experience their site in two ways: a moderated usability study, or the
support inbox after launch. The study costs **$40,000 to $150,000**, needs **2 to 6 weeks**, and recruits
**5 to 10 people** at about **$171 each**. Most teams skip it, ship, and read the complaints later.

Meanwhile the visitor mix is changing under them. **AI-referred traffic to US retail sites grew 393% year over
year in Q1 2026**, and by July those visits **converted 60% better than non-AI traffic** with **53% more revenue
per visit**. The customer is increasingly an agent, and no existing tool can tell a site owner whether an
agent can reach checkout. Static "agent readiness" checkers score robots.txt and never run anything.

The cost of not knowing is already measured: cart abandonment averages **70%**, and **18% of shoppers abandon
solely because of checkout UX**. QA is roughly **40% of software development cost**, and it still misses this,
because scripted tests check what the developer expected, not what the customer does.

## What Iris does [pick one angle]

**Angle A, the usability study that runs itself (recommended).**
Give Iris a URL. It researches who your real customers are from reviews, forums and help centres, maps what
your live site lets them do, builds eight evidence-backed personas, and sends them through the site at once on
real cloud browsers: on mobile, as returning visitors, from other countries, with different kinds of agent. In
minutes you get a readiness score and a ranked list of flags, each with the customer quote that predicted it,
the replay frozen on the frame where the agent gave up, and a concrete fix. One run replaces the study, for the
price of eight browser sessions.

**Angle B, agent-readiness, measured with real agents.**
Your next customer is an agent. Iris is the first tool that measures whether your site survives the agents
that are actually arriving, by running a controlled population of them and attributing every failure to the
one variable that caused it. Cloudflare tells you whether you published llms.txt. Iris tells you whether an
agent can check out.

**Angle C, pre-deploy customer simulation.**
See how your customers will use a release, and where they get stuck, before you ship it. Point Iris at a
staging URL and watch eight customers try. Caution on wording: the personas are reconstructed from real
quotes and the agents are real browsers doing real tasks, so "simulated users" undersells it and invites the
"how do you know that's real?" question. Prefer "send your customers in before your customers do."

Recommendation: lead with A for the room, use B's line for the Steel judges, keep C's promise ("before you
deploy") as one sentence inside A.

## How it works

1. **Input.** One field: the URL. No task list, no logins, no brief.
2. **Learning.** Two agents in parallel. Consumer research opens review sites, Reddit, help centres and one
   competitor in concurrent Steel sessions and collects real quotes with links. Site analysis is a read-only
   crawler that maps the live site into a few executable journeys.
3. **Test brief.** One Claude call turns the evidence pack and site map into eight personas: segment, device,
   country, identity, goal, and the supporting quote. Two personas differ in exactly one variable, so at least
   one finding is provably attributable.
4. **Swarm.** Eight Steel sessions at once, each with its own mobile fingerprint, residential geo proxy and
   persistent profile. A DOM agent (Browser Use) or a vision agent (Claude computer use) runs the goal and
   narrates every step. Agents never submit payment.
5. **Report.** Every stall is classified into a fixed failure taxonomy, attributed to a single variable, matched
   to the quote that predicted it, and given a proposed fix. Ranked by customers affected.

A flag is only reported if an agent actually reproduced it. Tooling failures are bucketed as harness errors
and excluded from the score.

## Why it needs Steel

Three things in the swarm cannot be faked from a laptop: a real mobile device fingerprint, a residential IP in
another country, and a browser identity that remembers its last visit. Those are Steel's mobile mode, geo
proxies and persistent profiles, and they are what turn "the agent failed" into "fails only on mobile" or
"fails only from Canada." The live viewer embeds are the swarm grid; session replay and Agent Traces are the
jump-to-failure in the report. Remove Steel and the product does not exist.

**Steel Computer (stretch, the $500 use case).** A stall becomes a fix: a Steel Computer clones the store,
applies the proposed patch, restarts the server, and re-runs the failing persona so the score climbs live. The
agent needs its own machine because fixing and re-testing requires a terminal, a filesystem and a process,
not just a browser.

## Why now

AI-referred retail traffic is up more than 14× since October 2024 and now outconverts humans. Adobe finds
30 to 40% of content on retailers' highest-value pages is still invisible to AI. The WebAIM Million 2026
report found **95.9% of the top million home pages fail basic accessibility checks**, with 56 errors per
page, and the same unlabelled buttons and unreachable overlays that block screen readers block agents. McKinsey
puts agentic commerce at **$3 to 5 trillion by 2030**. Every one of those sites needs to know if the agent
makes it to checkout, and the only way to know is to send one.

## What we built in 24 hours

- Backend: Steel session lifecycle, two agent engines on one event contract, a wave scheduler that warms
  persistent profiles before the returning variants run, a deterministic-first scorer with attribution and
  engine consensus. 102 unit tests that run with no keys or credits.
- Live on Steel today: Browser Use and Claude computer use runs, mobile mode, a profile handoff between
  sessions, and a cancel path that released every session.
- Front end: five screens driven by a typed event stream, playing an authored IKEA Canada run: readiness 61,
  three attributed flags, including a product page where the first "Add to cart" button adds a $499 mattress
  instead of the bed frame.

## Business

A usability study is bought once a quarter because it costs $40,000 and six weeks. Iris costs eight browser
sessions and a few dozen model calls, so it runs on every deploy. Pricing follows the study it replaces: per
run for teams, per seat with a CI check for platforms. First customers are mid-size e-commerce stores that
already pay for CRO consulting; the wedge is the agentic-commerce question their board is about to ask.

## The ask

Point Iris at your site. Give us the URL.

---

## Metrics on file (with sources)

| Metric | Number | Source |
|---|---|---|
| AI-referred traffic to US retail, Q1 2026 YoY | +393% (+693% over holiday 2025) | [Adobe via Yahoo Finance](https://finance.yahoo.com/sectors/technology/articles/ai-traffic-us-retailers-jumps-160141756.html) |
| AI-referred visits vs non-AI conversion, July 2026 | +60% conversion, +53% revenue per visit, +28% add-to-cart | [Digital Commerce 360 / Adobe](https://www.digitalcommerce360.com/2026/08/19/adobe-ai-referral-traffic-data-july-2026/) |
| Growth since Oct 2024 | more than 14× | [Digital Commerce 360](https://www.digitalcommerce360.com/2026/06/17/adobe-ai-referred-traffic-to-retail-sites-doubles-in-a-year/) |
| Retail page content invisible to AI | 30 to 40% | [Adobe](https://business.adobe.com/blog/ai-traffic-surge-retail-sites-not-machine-readable) |
| Agentic commerce by 2030 | $3 to 5 trillion | [McKinsey via Digital Commerce 360](https://www.digitalcommerce360.com/2025/10/20/mckinsey-forecast-5-trillion-agentic-commerce-sales-2030/) |
| Moderated usability study | $40k, up to $150k | [Nielsen Norman Group](https://www.nngroup.com/consulting/user-testing/) |
| Recruiting cost | ~$171 per participant | [NN/g](https://www.nngroup.com/articles/recruiting-test-participants-for-usability-studies/) |
| Study duration | 2 to 6 weeks | [CleverX](https://cleverx.com/guides/how-long-does-user-research-take-timelines-by-method-and-industry/) |
| Cart abandonment | 70.22% average; 18% abandon due to checkout UX alone | [Baymard](https://baymard.com/lists/cart-abandonment-rate), [Baymard checkout research](https://baymard.com/research/checkout-usability) |
| QA share of development cost | ~40%; 40% of large enterprises spend >25% of budget on testing | [TestGrid](https://testgrid.io/blog/software-testing-statistics/), [Panto](https://www.getpanto.ai/blog/software-testing-statistics) |
| Software testing market 2026 | ~$58B | [Panto](https://www.getpanto.ai/blog/software-testing-statistics) |
| Top 1M home pages failing WCAG, 2026 | 95.9%, 56 errors per page | [WebAIM Million 2026](https://webaim.org/projects/million/) |
