"""Turns a stalled RunResult into (FailureCategory, one-line description).

Order: RunResult.stall_hint (authoritative, from the Runner) -> deterministic content signals,
most-specific-first -> one LLM pass over the final screenshot + last 5 events for whatever's
left -> "other" if even the LLM call fails.

The specific content signals (captcha/cookie_wall/geo_block) are checked before the generic
URL-unchanged fallback deliberately: fixtures/run_result_stalled.json's URL never changes across
any of its steps (stuck behind #consent-modal at the same URL throughout), so checking
URL-unchanged first would misclassify a cookie wall as a timeout. High-precision signals win.
"""
from __future__ import annotations

import base64
import logging
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Protocol, runtime_checkable

from ..schemas import FailureCategory, RunEvent, RunResult

log = logging.getLogger("crucible.scorer.classify")

URL_STALL_STEPS = 4  # last N step_ok events with an unchanged URL and no other signal -> "timeout"

CAPTCHA_RE = re.compile(r"captcha|hcaptcha|recaptcha|turnstile", re.IGNORECASE)
COOKIE_WALL_RE = re.compile(r"intercept\w*\s+by\s+overlay.{0,60}?(cookie|consent)", re.IGNORECASE)
GEO_BLOCK_RE = re.compile(
    r"not available in (your|this) (country|region)|blocked in (your|this) (country|region)|"
    r"geo-?block|vpn detected|access (denied|restricted).{0,30}(country|region)",
    re.IGNORECASE,
)

REMAINING_CATEGORIES: tuple[FailureCategory, ...] = (
    "hidden_nav", "icon_only_control", "ambiguous_cta", "infinite_scroll", "login_wall",
    "layout_shift", "other",
)
CLASSIFY_SYSTEM = (
    "You classify why an AI web agent got stuck on a task. Reply with EXACTLY one line: "
    "CATEGORY: <one of hidden_nav|icon_only_control|ambiguous_cta|infinite_scroll|login_wall|"
    "layout_shift|other> | DESCRIPTION: <one sentence, mention the specific element or control involved>."
)
_PARSE_RE = re.compile(r"CATEGORY:\s*(\w+)\s*\|\s*DESCRIPTION:\s*(.+)", re.IGNORECASE)


@runtime_checkable
class Classifier(Protocol):
    """LLM fallback contract.

    Rules:
      * never raise; on any failure return ("other", <short reason>)
      * receives the final screenshot bytes (or None if unreadable) and the full RunResult
    """

    async def classify(self, result: RunResult, screenshot: bytes | None) -> tuple[FailureCategory, str]: ...


def _url_of(ev: RunEvent) -> str | None:
    m = re.search(r"https?://\S+", ev.observation)
    return m.group(0) if m else None


def classify_deterministic(result: RunResult) -> tuple[FailureCategory, str] | None:
    """Cheap, explainable checks. None means "fall through to the LLM"."""
    if result.stall_hint in ("step_cap", "run_budget"):
        return "timeout", f"The agent hit the {result.stall_hint.replace('_', ' ')} without finishing the journey."
    blob = "\n".join(f"{e.action}\n{e.observation}" for e in result.events)
    if CAPTCHA_RE.search(blob):
        return "captcha", "A CAPTCHA challenge blocked the agent from proceeding."
    if COOKIE_WALL_RE.search(blob):
        return "cookie_wall", "A cookie/consent overlay intercepted clicks and the agent could not dismiss it."
    if GEO_BLOCK_RE.search(blob):
        return "geo_block", "The site returned a geo-block page for this country."
    step_ok = [e for e in result.events if e.outcome == "step_ok"]
    tail = step_ok[-URL_STALL_STEPS:]
    if len(tail) == URL_STALL_STEPS:
        urls = {_url_of(e) for e in tail}
        if len(urls) == 1 and None not in urls:
            return "timeout", f"The URL did not change over the last {URL_STALL_STEPS} actions; the agent appears stuck."
    return None


def _read_screenshot(ref: str | None) -> bytes | None:
    if not ref:
        return None
    try:
        return Path(ref).read_bytes()
    except OSError:
        return None


@dataclass
class LLMClassifier:
    model: str = "claude-sonnet-5"
    max_tokens: int = 300

    def _client(self):
        import anthropic

        return anthropic.AsyncAnthropic()

    async def classify(self, result: RunResult, screenshot: bytes | None) -> tuple[FailureCategory, str]:
        try:
            client = self._client()
            tail = result.events[-5:]
            events_text = "\n".join(f"step {e.step_index}: {e.action} -> {e.observation}" for e in tail)
            content: list[dict] = [
                {"type": "text", "text": f"Journey: {result.journey_id}\nLast steps:\n{events_text}\n\nWhy did the agent get stuck?"}
            ]
            if screenshot is not None:
                content.append(
                    {"type": "image", "source": {"type": "base64", "media_type": "image/png", "data": base64.b64encode(screenshot).decode()}}
                )
            resp = await client.messages.create(
                model=self.model, max_tokens=self.max_tokens,
                system=CLASSIFY_SYSTEM, messages=[{"role": "user", "content": content}],
            )
            text = "".join(b.text for b in resp.content if getattr(b, "type", "") == "text")
            m = _PARSE_RE.search(text)
            if not m:
                return "other", (text.strip()[:200] or "Could not determine the cause; see replay.")
            cat = m.group(1).lower()
            return (cat if cat in REMAINING_CATEGORIES else "other"), m.group(2).strip()[:200]
        except Exception as e:  # noqa: BLE001 - LLM call failing must never crash score()
            log.warning("LLM classification failed for %s: %s", result.run_id, e)
            return "other", "Automatic classification failed; needs manual review."


async def classify(result: RunResult, *, llm: Classifier | None = None) -> tuple[FailureCategory, str]:
    det = classify_deterministic(result)
    if det is not None:
        return det
    classifier = llm or LLMClassifier()
    try:
        return await classifier.classify(result, _read_screenshot(result.final_screenshot_ref))
    except Exception as e:  # noqa: BLE001 - defense in depth even if a custom Classifier misbehaves
        log.warning("classifier raised for %s: %s", result.run_id, e)
        return "other", "Automatic classification failed; needs manual review."
