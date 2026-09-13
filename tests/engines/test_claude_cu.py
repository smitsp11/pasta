"""Claude CU dispatch and history pruning, with a fake Playwright page (no model calls)."""
from types import SimpleNamespace

from crucible.engines.claude_cu import ClaudeComputerUseEngine, _key_combo


class FakeMouse:
    def __init__(self, log): self.log = log
    async def click(self, x, y, button="left", click_count=1): self.log.append(("click", x, y, button, click_count))
    async def move(self, x, y, steps=1): self.log.append(("move", x, y))
    async def down(self): self.log.append(("down",))
    async def up(self): self.log.append(("up",))
    async def wheel(self, dx, dy): self.log.append(("wheel", dx, dy))


class FakeKeyboard:
    def __init__(self, log): self.log = log
    async def type(self, text, delay=0): self.log.append(("type", text))
    async def press(self, combo): self.log.append(("press", combo))
    async def down(self, k): self.log.append(("kdown", k))
    async def up(self, k): self.log.append(("kup", k))


def fake_page(log):
    return SimpleNamespace(mouse=FakeMouse(log), keyboard=FakeKeyboard(log), url="https://x.test/")


def engine():
    return ClaudeComputerUseEngine(action_settle_s=0)


async def test_click_clamps_to_display():
    log = []
    err = await engine()._do(fake_page(log), {"action": "left_click", "coordinate": [5000, -3]}, 1280, 800)
    assert err is None and log == [("click", 1279, 0, "left", 1)]


async def test_double_click_and_right_click():
    log = []
    e = engine()
    await e._do(fake_page(log), {"action": "double_click", "coordinate": [10, 10]}, 100, 100)
    await e._do(fake_page(log), {"action": "right_click", "coordinate": [10, 10]}, 100, 100)
    assert log == [("click", 10, 10, "left", 2), ("click", 10, 10, "right", 1)]


async def test_scroll_direction_and_amount():
    log = []
    await engine()._do(fake_page(log), {"action": "scroll", "coordinate": [50, 50], "scroll_direction": "up",
                                        "scroll_amount": 2}, 100, 100)
    assert log == [("move", 50, 50), ("wheel", 0, -200)]


async def test_type_and_key_combo():
    log = []
    e = engine()
    await e._do(fake_page(log), {"action": "type", "text": "trail jacket"}, 100, 100)
    await e._do(fake_page(log), {"action": "key", "text": "ctrl+a"}, 100, 100)
    await e._do(fake_page(log), {"action": "key", "text": "Return"}, 100, 100)
    assert log == [("type", "trail jacket"), ("press", "Control+a"), ("press", "Enter")]


def test_key_combo_mapping():
    assert _key_combo("cmd+shift+p") == "Meta+Shift+p"
    assert _key_combo("Escape") == "Escape"
    assert _key_combo("Page_Down") == "Page_Down"   # unknown names pass through


async def test_unsupported_action_reports_not_raises():
    log = []
    err = await engine()._do(fake_page(log), {"action": "teleport"}, 100, 100)
    assert err and "unsupported" in err and log == []


async def test_playwright_error_is_reported_to_model():
    log = []
    page = fake_page(log)

    async def boom(*a, **k): raise TimeoutError("element detached")
    page.mouse.click = boom
    err = await engine()._do(page, {"action": "left_click", "coordinate": [1, 1]}, 10, 10)
    assert err and "TimeoutError" in err


def test_prune_images_keeps_newest():
    e = ClaudeComputerUseEngine(keep_images=2)
    img = lambda: {"type": "image", "source": {"type": "base64", "media_type": "image/png", "data": "x"}}  # noqa: E731
    msgs = []
    for i in range(4):
        msgs.append({"role": "assistant", "content": [{"type": "tool_use", "id": f"t{i}", "name": "computer", "input": {}}]})
        msgs.append({"role": "user", "content": [{"type": "tool_result", "tool_use_id": f"t{i}", "content": [img()]}]})
    e._prune_images(msgs)
    kept = [m for m in msgs if m["role"] == "user" and m["content"][0]["content"][0]["type"] == "image"]
    assert len(kept) == 2
    assert msgs[1]["content"][0]["content"][0]["type"] == "text"      # oldest pruned
    assert msgs[-1]["content"][0]["content"][0]["type"] == "image"    # newest kept
