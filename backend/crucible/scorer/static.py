"""Cloudflare/isitagentready static agent-readiness score, shown beside ours for contrast.

No confirmed public API is documented anywhere in this repo (docs/concept.md references
https://isitagentready.com only as a human-facing URL). fetch_static_score degrades to None on
ANY failure -- missing endpoint, network error, unexpected response shape -- per the design
doc: "If the Cloudflare static score cannot be fetched, the contrast panel is simply hidden."
The actual HTTP call is isolated in _fetch_raw so it can be filled in after a research spike
without touching any caller; until that spike confirms a real, documented endpoint, _fetch_raw
returning None IS the correct, honest implementation of the fallback the design doc asks for --
not a stub blocking anything else in crucible/scorer/.
"""
from __future__ import annotations

import logging
from typing import Awaitable, Callable

log = logging.getLogger("crucible.scorer.static")

FetchFn = Callable[[str], Awaitable[dict | None]]


async def _fetch_raw(url: str) -> dict | None:
    """Isolated network call. TODO after the research spike: an HTTP GET against the confirmed
    endpoint. Until then this must not guess a URL -- return None."""
    return None


def _parse_score(payload: dict) -> float | None:
    try:
        val = payload.get("score")
        return float(val) if val is not None else None
    except (TypeError, ValueError):
        return None


async def fetch_static_score(url: str, *, fetch: FetchFn = _fetch_raw) -> float | None:
    try:
        payload = await fetch(url)
        return _parse_score(payload) if payload is not None else None
    except Exception as e:  # noqa: BLE001 - a flaky external API must never break scoring
        log.info("static score fetch failed for %s: %s", url, e)
        return None
