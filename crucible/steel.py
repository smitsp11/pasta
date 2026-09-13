"""Steel session lifecycle: create -> connect over CDP -> release (idempotent).

Verified against steel-sdk 0.19.0:
  * session lifetime kwarg is `api_timeout` (ms); `timeout` is the HTTP timeout.
  * mobile: device_config={"device": "mobile"}; geo: use_proxy={"geolocation": {"country": cc}}
  * profiles: sessions.create(persist_profile=True) -> session.profile_id; the snapshot uploads
    after release and profiles.get(id).status moves UPLOADING -> READY.
"""
from __future__ import annotations

import argparse
import asyncio
import logging
import os
import sys
from contextlib import asynccontextmanager
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, AsyncIterator, Awaitable, Callable

from dotenv import load_dotenv

from .schemas import Config

log = logging.getLogger("crucible.steel")

DESKTOP_DIMENSIONS = {"width": 1280, "height": 800}
DEFAULT_TIMEOUT_MS = 12 * 60_000       # under Steel's 15-minute cap
DEFAULT_INACTIVITY_MS = 120_000        # release a hung engine's session early
HLS_URL = "https://api.steel.dev/v1/sessions/{id}/hls"
RUNS_DIR = Path(os.environ.get("CRUCIBLE_RUNS_DIR", "runs"))


class SteelUnavailable(Exception):
    """Session could not be created or connected. The Runner maps this to harness_error."""


def get_client():
    """AsyncSteel from STEEL_API_KEY (loads .env). Imported lazily so tests never need the SDK."""
    load_dotenv()
    key = os.environ.get("STEEL_API_KEY")
    if not key:
        raise SteelUnavailable("STEEL_API_KEY is not set")
    from steel import AsyncSteel
    return AsyncSteel(steel_api_key=key)


def session_kwargs(cfg: Config, *, profile_id: str | None = None, persist_profile: bool = False,
                   timeout_ms: int = DEFAULT_TIMEOUT_MS, inactivity_ms: int = DEFAULT_INACTIVITY_MS) -> dict[str, Any]:
    """Pure mapping from a population Config to `sessions.create` kwargs."""
    kw: dict[str, Any] = {
        "api_timeout": timeout_ms,
        "inactivity_timeout": inactivity_ms,
        "solve_captcha": False,          # a CAPTCHA is a finding, not something to solve away
    }
    if cfg.device == "mobile":
        kw["device_config"] = {"device": "mobile"}
    else:
        kw["dimensions"] = dict(DESKTOP_DIMENSIONS)
    if cfg.country and cfg.country.upper() != "US":
        kw["use_proxy"] = {"geolocation": {"country": cfg.country.upper()}}
    if profile_id:
        kw["profile_id"] = profile_id
    if persist_profile:
        kw["persist_profile"] = True
    return kw


def cdp_url(websocket_url: str, api_key: str) -> str:
    sep = "&" if "?" in websocket_url else "?"
    return f"{websocket_url}{sep}apiKey={api_key}"


class SteelSession:
    """One live Steel browser session with a Playwright page attached over CDP.

    Use via `open_session(...)`; construct directly only in tests.
    """

    def __init__(self, client: Any, session: Any, api_key: str, *,
                 connector: Callable[["SteelSession"], Awaitable[None]] | None = None):
        self._client = client
        self._raw = session
        self._api_key = api_key
        self._connector = connector or _playwright_connect
        self._released = False
        self._release_lock = asyncio.Lock()
        self._pw = None
        self._browser = None
        self.page = None
        self.session_id: str = session.id
        self.websocket_url: str = session.websocket_url
        self.cdp_url: str = cdp_url(session.websocket_url, api_key)
        self.viewer_url: str = f"{session.debug_url}?interactive=false"
        self.replay_url: str = session.session_viewer_url
        self.hls_url: str = HLS_URL.format(id=session.id)
        self.profile_id: str | None = getattr(session, "profile_id", None)
        created = getattr(session, "created_at", None)
        self.created_at: datetime = created if isinstance(created, datetime) else datetime.now(timezone.utc)
        if self.created_at.tzinfo is None:
            self.created_at = self.created_at.replace(tzinfo=timezone.utc)
        dims = getattr(session, "dimensions", None)
        self.dimensions: tuple[int, int] = (
            (int(dims.width), int(dims.height)) if dims is not None and getattr(dims, "width", None)
            else (DESKTOP_DIMENSIONS["width"], DESKTOP_DIMENSIONS["height"])
        )
        self.screenshot_dir: Path = RUNS_DIR / self.session_id

    # -- lifecycle -----------------------------------------------------------

    async def connect(self) -> "SteelSession":
        try:
            await self._connector(self)
        except Exception as e:
            await self.release()
            raise SteelUnavailable(f"CDP connect failed for {self.session_id}: {e}") from e
        return self

    async def release(self) -> None:
        """Idempotent. Closes Playwright first, then releases the Steel session."""
        async with self._release_lock:
            if self._released:
                return
            self._released = True
            try:
                if self._browser is not None:
                    await self._browser.close()
            except Exception as e:  # noqa: BLE001
                log.debug("browser close on %s: %s", self.session_id, e)
            try:
                if self._pw is not None:
                    await self._pw.stop()
            except Exception as e:  # noqa: BLE001
                log.debug("playwright stop on %s: %s", self.session_id, e)
            try:
                await self._client.sessions.release(self.session_id)
                log.info("released steel session %s", self.session_id)
            except Exception as e:  # noqa: BLE001
                # Already released (timeout, inactivity) is fine; anything else is logged, never raised.
                log.warning("release of %s returned %s", self.session_id, e)
            await self._log_credits()

    async def _log_credits(self) -> None:
        """Append credits/proxy usage to runs/credits.log so the budget is visible during the event."""
        try:
            s = await self._client.sessions.retrieve(self.session_id)
            line = (f"{datetime.now(timezone.utc).isoformat(timespec='seconds')} {self.session_id} "
                    f"credits={getattr(s, 'credits_used', '?')} proxy_bytes={getattr(s, 'proxy_bytes_used', '?')} "
                    f"duration_ms={getattr(s, 'duration', '?')} reason={getattr(s, 'release_reason', '?')}\n")
            RUNS_DIR.mkdir(parents=True, exist_ok=True)
            with open(RUNS_DIR / "credits.log", "a") as f:
                f.write(line)
        except Exception as e:  # noqa: BLE001
            log.debug("credits log for %s skipped: %s", self.session_id, e)

    @property
    def released(self) -> bool:
        return self._released

    async def credits_used(self) -> int | None:
        try:
            s = await self._client.sessions.retrieve(self.session_id)
            return getattr(s, "credits_used", None)
        except Exception:  # noqa: BLE001
            return None

    # -- helpers for engines ------------------------------------------------

    def replay_offset_s(self, ts: datetime) -> float:
        if ts.tzinfo is None:
            ts = ts.replace(tzinfo=timezone.utc)
        return max(0.0, (ts - self.created_at).total_seconds())

    async def screenshot_ref(self, step_index: int) -> str | None:
        """Screenshot the attached page to runs/<session>/<step>.png; returns the path."""
        if self.page is None:
            return None
        try:
            self.screenshot_dir.mkdir(parents=True, exist_ok=True)
            path = self.screenshot_dir / f"{step_index:03d}.png"
            await self.page.screenshot(path=str(path))
            return str(path)
        except Exception as e:  # noqa: BLE001
            log.debug("screenshot failed on %s step %s: %s", self.session_id, step_index, e)
            return None

    def save_screenshot_bytes(self, step_index: int, png: bytes) -> str:
        self.screenshot_dir.mkdir(parents=True, exist_ok=True)
        path = self.screenshot_dir / f"{step_index:03d}.png"
        path.write_bytes(png)
        return str(path)

    @property
    def url(self) -> str:
        try:
            return self.page.url if self.page is not None else ""
        except Exception:  # noqa: BLE001
            return ""


async def _playwright_connect(s: SteelSession) -> None:
    from playwright.async_api import async_playwright
    s._pw = await async_playwright().start()
    s._browser = await s._pw.chromium.connect_over_cdp(s.cdp_url)
    ctx = s._browser.contexts[0] if s._browser.contexts else await s._browser.new_context()
    s.page = ctx.pages[0] if ctx.pages else await ctx.new_page()


@asynccontextmanager
async def open_session(cfg: Config, *, profile_id: str | None = None, persist_profile: bool = False,
                       timeout_ms: int = DEFAULT_TIMEOUT_MS, inactivity_ms: int = DEFAULT_INACTIVITY_MS,
                       client: Any = None, connect: bool = True) -> AsyncIterator[SteelSession]:
    """Create a Steel session for `cfg`, attach Playwright, and always release on exit."""
    client = client or get_client()
    api_key = os.environ.get("STEEL_API_KEY", "")
    kw = session_kwargs(cfg, profile_id=profile_id, persist_profile=persist_profile,
                        timeout_ms=timeout_ms, inactivity_ms=inactivity_ms)
    try:
        raw = await client.sessions.create(**kw)
    except Exception as e:
        raise SteelUnavailable(f"sessions.create failed for {cfg.label}: {e}") from e
    session = SteelSession(client, raw, api_key)
    log.info("created steel session %s for %s (%s)", session.session_id, cfg.label, kw)
    try:
        if connect:
            await session.connect()
        yield session
    finally:
        await session.release()


async def wait_profile_ready(profile_id: str, *, timeout_s: float = 90.0, poll_s: float = 3.0,
                             client: Any = None) -> bool:
    """Poll profiles.get until status == READY. Returns False on timeout or FAILED."""
    client = client or get_client()
    deadline = asyncio.get_event_loop().time() + timeout_s
    while True:
        try:
            p = await client.profiles.get(profile_id)
            status = str(getattr(p, "status", "")).upper()
        except Exception as e:  # noqa: BLE001
            log.debug("profiles.get(%s): %s", profile_id, e)
            status = ""
        if status == "READY":
            return True
        if status == "FAILED":
            log.warning("profile %s FAILED", profile_id)
            return False
        if asyncio.get_event_loop().time() >= deadline:
            log.warning("profile %s not READY after %.0fs (last status %r)", profile_id, timeout_s, status)
            return False
        await asyncio.sleep(poll_s)


async def release_all(client: Any = None) -> None:
    client = client or get_client()
    r = await client.sessions.release_all()
    log.info("release_all: %s", getattr(r, "message", r))


async def list_live(client: Any = None) -> list[Any]:
    client = client or get_client()
    r = await client.sessions.list()
    sessions = getattr(r, "sessions", r)
    return [s for s in sessions if getattr(s, "status", "") == "live"]


def _main() -> int:
    ap = argparse.ArgumentParser(prog="python -m crucible.steel")
    ap.add_argument("--release-all", action="store_true", help="release every live session (panic button)")
    ap.add_argument("--list", action="store_true", help="list live sessions")
    a = ap.parse_args()
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(name)s: %(message)s")
    if a.release_all:
        asyncio.run(release_all())
    elif a.list:
        for s in asyncio.run(list_live()):
            print(s.id, s.status, getattr(s, "created_at", ""), s.session_viewer_url)
    else:
        ap.print_help()
    return 0


if __name__ == "__main__":
    sys.exit(_main())
