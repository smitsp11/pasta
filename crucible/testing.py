"""Fakes shared by tests, the fixture generator, and `--fake` dry runs. No Steel, no model."""
from __future__ import annotations

import asyncio
from contextlib import asynccontextmanager
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from types import SimpleNamespace

from .schemas import Config
from .steel import SteelSession


def raw_session(sid: str = "sess-1", profile_id: str | None = None, created_at: datetime | None = None):
    return SimpleNamespace(
        id=sid, websocket_url=f"wss://connect.steel.dev?sessionId={sid}",
        debug_url=f"https://app.steel.dev/sessions/{sid}/debug",
        session_viewer_url=f"https://app.steel.dev/sessions/{sid}",
        profile_id=profile_id, created_at=created_at or datetime.now(timezone.utc),
        dimensions=SimpleNamespace(width=1280, height=800), status="live", credits_used=3,
    )


class FakeSteelClient:
    """Records every call; profile status is scripted."""

    def __init__(self, profile_status: list[str] | None = None, fail_create: bool = False):
        self.created: list[dict] = []
        self.released: list[str] = []
        self.fail_create = fail_create
        self._profile_status = list(profile_status or ["READY"])
        self._n = 0
        self.sessions = SimpleNamespace(create=self._create, release=self._release,
                                        retrieve=self._retrieve, release_all=self._release_all,
                                        list=self._list)
        self.profiles = SimpleNamespace(get=self._profile_get)

    async def _create(self, **kw):
        if self.fail_create:
            raise RuntimeError("quota exceeded")
        self._n += 1
        self.created.append(kw)
        pid = f"prof-{self._n}" if kw.get("persist_profile") else kw.get("profile_id")
        return raw_session(f"sess-{self._n}", profile_id=pid)

    async def _release(self, sid):
        self.released.append(sid)
        return SimpleNamespace(success=True, message="released")

    async def _retrieve(self, sid):
        return raw_session(sid)

    async def _release_all(self):
        return SimpleNamespace(success=True, message="all released")

    async def _list(self):
        return SimpleNamespace(sessions=[])

    async def _profile_get(self, pid):
        status = self._profile_status.pop(0) if len(self._profile_status) > 1 else self._profile_status[0]
        return SimpleNamespace(id=pid, status=status)


async def no_connect(_s: SteelSession) -> None:
    """Connector stub: no Playwright."""


async def _noop_credits() -> None:
    return None


async def profile_ready(_pid: str) -> bool:
    await asyncio.sleep(0.01)
    return True


@dataclass
class FakeSessionFactory:
    """open_session-like factory backed by FakeSteelClient; tracks concurrency."""
    client: FakeSteelClient = field(default_factory=FakeSteelClient)
    open_now: int = 0
    max_open: int = 0
    opened: list[SteelSession] = field(default_factory=list)
    fail_labels: set[str] = field(default_factory=set)
    screenshot_root: Path = Path("/tmp/crucible-fake")

    def __call__(self, cfg: Config, *, profile_id=None, persist_profile=False, **_):
        return self._open(cfg, profile_id, persist_profile)

    @asynccontextmanager
    async def _open(self, cfg, profile_id, persist_profile):
        from .steel import SteelUnavailable, session_kwargs
        if cfg.label in self.fail_labels:
            raise SteelUnavailable(f"simulated create failure for {cfg.label}")
        kw = session_kwargs(cfg, profile_id=profile_id, persist_profile=persist_profile)
        raw = await self.client.sessions.create(**kw)
        s = SteelSession(self.client, raw, "test-key", connector=no_connect)
        s.screenshot_dir = self.screenshot_root / s.session_id
        s._log_credits = _noop_credits   # fake sessions never touch runs/credits.log
        self.opened.append(s)
        self.open_now += 1
        self.max_open = max(self.max_open, self.open_now)
        try:
            await s.connect()
            yield s
        finally:
            self.open_now -= 1
            await s.release()
