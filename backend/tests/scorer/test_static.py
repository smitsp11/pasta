from crucible.scorer.static import fetch_static_score


async def test_default_fetch_degrades_to_none_with_no_confirmed_endpoint():
    assert await fetch_static_score("https://example.test") is None


async def test_valid_payload_returns_score():
    async def fetch(url: str):
        return {"score": 85.0}

    assert await fetch_static_score("https://x", fetch=fetch) == 85.0


async def test_none_payload_returns_none():
    async def fetch(url: str):
        return None

    assert await fetch_static_score("https://x", fetch=fetch) is None


async def test_missing_score_key_returns_none():
    async def fetch(url: str):
        return {}

    assert await fetch_static_score("https://x", fetch=fetch) is None


async def test_malformed_score_value_returns_none_not_raise():
    async def fetch(url: str):
        return {"score": "not-a-number"}

    assert await fetch_static_score("https://x", fetch=fetch) is None


async def test_fetch_raising_returns_none_not_raise():
    async def fetch(url: str):
        raise ConnectionError("network down")

    assert await fetch_static_score("https://x", fetch=fetch) is None


async def test_integer_score_is_coerced_to_float():
    async def fetch(url: str):
        return {"score": 90}

    result = await fetch_static_score("https://x", fetch=fetch)
    assert result == 90.0 and isinstance(result, float)
