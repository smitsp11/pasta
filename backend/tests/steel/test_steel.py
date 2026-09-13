import asyncio

import pytest

from crucible.schemas import Config
from crucible.steel import (SteelSession, SteelUnavailable, cdp_url, open_session, session_kwargs,
                            wait_profile_ready)
from tests.conftest import FakeSteelClient, no_connect, raw_session


def test_session_kwargs_baseline():
    kw = session_kwargs(Config())
    assert kw["api_timeout"] == 12 * 60_000
    assert kw["dimensions"] == {"width": 1280, "height": 800}
    assert kw["solve_captcha"] is False
    assert "use_proxy" not in kw and "device_config" not in kw and "profile_id" not in kw


def test_session_kwargs_variants():
    assert session_kwargs(Config(device="mobile"))["device_config"] == {"device": "mobile"}
    assert "dimensions" not in session_kwargs(Config(device="mobile"))
    assert session_kwargs(Config(country="ca"))["use_proxy"] == {"geolocation": {"country": "CA"}}
    kw = session_kwargs(Config(identity="returning"), profile_id="prof-9")
    assert kw["profile_id"] == "prof-9" and "persist_profile" not in kw
    assert session_kwargs(Config(), persist_profile=True)["persist_profile"] is True


def test_cdp_url_appends_key():
    assert cdp_url("wss://x?sessionId=1", "K") == "wss://x?sessionId=1&apiKey=K"
    assert cdp_url("wss://x", "K") == "wss://x?apiKey=K"


async def test_release_is_idempotent():
    client = FakeSteelClient()
    s = SteelSession(client, raw_session("s1"), "k", connector=no_connect)
    await s.release()
    await s.release()
    assert client.released == ["s1"]


async def test_open_session_releases_on_exception(factory=None):
    client = FakeSteelClient()
    with pytest.raises(RuntimeError):
        async with open_session(Config(), client=client, connect=False):
            raise RuntimeError("boom")
    assert client.released == ["sess-1"]


async def test_open_session_releases_on_cancel():
    client = FakeSteelClient()

    async def body():
        async with open_session(Config(), client=client, connect=False):
            await asyncio.sleep(10)

    t = asyncio.create_task(body())
    await asyncio.sleep(0.01)
    t.cancel()
    with pytest.raises(asyncio.CancelledError):
        await t
    assert client.released == ["sess-1"]


async def test_connect_failure_releases_and_raises():
    client = FakeSteelClient()

    async def bad_connector(_s):
        raise ConnectionError("cdp down")

    s = SteelSession(client, raw_session("s2"), "k", connector=bad_connector)
    with pytest.raises(SteelUnavailable):
        await s.connect()
    assert client.released == ["s2"]


async def test_create_failure_is_steel_unavailable():
    client = FakeSteelClient(fail_create=True)
    with pytest.raises(SteelUnavailable):
        async with open_session(Config(), client=client, connect=False):
            pass


async def test_wait_profile_ready_polls_until_ready():
    client = FakeSteelClient(profile_status=["UPLOADING", "UPLOADING", "READY"])
    assert await wait_profile_ready("p", client=client, poll_s=0.001) is True


async def test_wait_profile_ready_times_out():
    client = FakeSteelClient(profile_status=["UPLOADING"])
    assert await wait_profile_ready("p", client=client, timeout_s=0.01, poll_s=0.001) is False


async def test_wait_profile_failed():
    client = FakeSteelClient(profile_status=["FAILED"])
    assert await wait_profile_ready("p", client=client, poll_s=0.001) is False


def test_replay_offset():
    from datetime import datetime, timezone
    s = SteelSession(FakeSteelClient(), raw_session("s3", created_at=datetime(2026, 9, 12, 12, 0, tzinfo=timezone.utc)),
                     "k", connector=no_connect)
    assert s.replay_offset_s(datetime(2026, 9, 12, 12, 1, 30, tzinfo=timezone.utc)) == 90.0
    assert s.replay_offset_s(datetime(2026, 9, 12, 11, 0, tzinfo=timezone.utc)) == 0.0
