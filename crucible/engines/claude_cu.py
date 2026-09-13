"""Claude computer use (vision agent) on a Steel session, driven through Playwright over CDP.

Tool: computer_20251124 with beta header computer-use-2025-11-24 (as in the Steel cookbook).
Model: claude-opus-5, adaptive thinking on by default, effort "high" (documented sweet spot
for computer use). Server-side refusal fallback is enabled by default; remove `fallbacks` if
you would rather handle `stop_reason == "refusal"` yourself.
"""
from __future__ import annotations

import asyncio
import base64
import logging
import os
import re
from typing import Any, AsyncIterator

from ..schemas import Config, Journey, RunEvent
from ..steel import SteelSession
from .base import PAYMENT_GUARD_PROMPT, RunContext

log = logging.getLogger("crucible.engines.claude_cu")

DEFAULT_MODEL = os.environ.get("CRUCIBLE_CLAUDE_CU_MODEL", "claude-opus-5")
BETAS = ["computer-use-2025-11-24", "server-side-fallback-2026-07-01"]
COMPLETED_RE = re.compile(r"TASK_COMPLETED\s*:?\s*(.*)", re.IGNORECASE | re.DOTALL)
FAILED_RE = re.compile(r"TASK_(FAILED|ABANDONED)\s*:?\s*(.*)", re.IGNORECASE | re.DOTALL)
KEYMAP = {"ctrl": "Control", "control": "Control", "cmd": "Meta", "command": "Meta", "super": "Meta",
          "alt": "Alt", "option": "Alt", "shift": "Shift", "return": "Enter", "enter": "Enter",
          "esc": "Escape", "escape": "Escape", "space": " ", "backspace": "Backspace", "tab": "Tab",
          "delete": "Delete", "up": "ArrowUp", "down": "ArrowDown", "left": "ArrowLeft", "right": "ArrowRight",
          "pageup": "PageUp", "pagedown": "PageDown", "home": "Home", "end": "End"}

SYSTEM = (
    "You are an autonomous web agent operating a real browser through screenshots. "
    "Work step by step: look at the screenshot, choose one action, observe the result. "
    "Use the computer tool for every interaction. Dismiss cookie banners if you can. "
    "When the task is complete, reply with a final message starting with 'TASK_COMPLETED:' and a one-line "
    "summary. If you are stuck after trying reasonable alternatives, reply with 'TASK_FAILED:' and the reason. "
    + PAYMENT_GUARD_PROMPT
)


def _key_combo(text: str) -> str:
    parts = [p.strip() for p in re.split(r"[+\-]", text) if p.strip()] or [text]
    mapped = [KEYMAP.get(p.lower(), p if len(p) > 1 else p) for p in parts]
    return "+".join(mapped)


class ClaudeComputerUseEngine:
    name = "claude_cu"
    default_step_cap = 40

    def __init__(self, model: str = DEFAULT_MODEL, *, effort: str = "high", max_tokens: int = 4096,
                 token_budget: int = 400_000, keep_images: int = 3, action_settle_s: float = 1.0):
        self.model = model
        self.effort = effort
        self.max_tokens = max_tokens
        self.token_budget = token_budget
        self.keep_images = keep_images
        self.action_settle_s = action_settle_s

    def _client(self):
        import anthropic
        return anthropic.AsyncAnthropic()

    # -- action dispatch ---------------------------------------------------

    async def _do(self, page, inp: dict[str, Any], w: int, h: int) -> str | None:
        """Execute one computer-tool action. Returns an error string or None."""
        act = inp.get("action")
        coord = inp.get("coordinate")
        x, y = (None, None)
        if isinstance(coord, (list, tuple)) and len(coord) == 2:
            x = min(max(int(coord[0]), 0), w - 1)
            y = min(max(int(coord[1]), 0), h - 1)
        try:
            if act == "screenshot":
                return None
            if act in ("left_click", "right_click", "middle_click", "double_click", "triple_click"):
                if x is None:
                    return "coordinate required"
                button = {"right_click": "right", "middle_click": "middle"}.get(act, "left")
                clicks = {"double_click": 2, "triple_click": 3}.get(act, 1)
                await page.mouse.click(x, y, button=button, click_count=clicks)
            elif act == "mouse_move":
                if x is None:
                    return "coordinate required"
                await page.mouse.move(x, y)
            elif act == "left_click_drag":
                sc = inp.get("start_coordinate") or [x, y]
                await page.mouse.move(int(sc[0]), int(sc[1]))
                await page.mouse.down()
                await page.mouse.move(x, y, steps=10)
                await page.mouse.up()
            elif act == "type":
                await page.keyboard.type(str(inp.get("text", "")), delay=20)
            elif act == "key":
                await page.keyboard.press(_key_combo(str(inp.get("text", ""))))
            elif act == "hold_key":
                await page.keyboard.down(_key_combo(str(inp.get("text", ""))))
                await asyncio.sleep(min(float(inp.get("duration", 1)), 3))
                await page.keyboard.up(_key_combo(str(inp.get("text", ""))))
            elif act == "scroll":
                if x is not None:
                    await page.mouse.move(x, y)
                amt = int(inp.get("scroll_amount", 3)) * 100
                d = str(inp.get("scroll_direction", "down"))
                dx, dy = {"down": (0, amt), "up": (0, -amt), "right": (amt, 0), "left": (-amt, 0)}.get(d, (0, amt))
                await page.mouse.wheel(dx, dy)
            elif act == "wait":
                await asyncio.sleep(min(float(inp.get("duration", 1)), 3))
            elif act == "zoom":
                return "zoom is not supported in this environment; take a screenshot instead"
            else:
                return f"unsupported action {act!r}"
        except Exception as e:  # noqa: BLE001 - report to the model, do not crash the run
            return f"{type(e).__name__}: {e}"
        await asyncio.sleep(self.action_settle_s)
        return None

    def _prune_images(self, messages: list[dict[str, Any]]) -> None:
        """Keep only the newest `keep_images` screenshots in history to bound token cost."""
        seen = 0
        for m in reversed(messages):
            if m["role"] != "user" or not isinstance(m["content"], list):
                continue
            for block in m["content"]:
                if block.get("type") != "tool_result":
                    continue
                content = block.get("content")
                if isinstance(content, list) and any(c.get("type") == "image" for c in content):
                    seen += 1
                    if seen > self.keep_images:
                        block["content"] = [{"type": "text", "text": "[earlier screenshot omitted]"}]

    # -- main loop ---------------------------------------------------------

    async def run_journey(self, session: SteelSession, journey: Journey, cfg: Config, step_cap: int,
                          ctx: RunContext) -> AsyncIterator[RunEvent]:
        page = session.page
        if page is None:
            raise RuntimeError("claude_cu requires a connected Playwright page")
        client = self._client()

        await page.goto(journey.entry_url, wait_until="domcontentloaded", timeout=30_000)
        try:
            w, h = await page.evaluate("[window.innerWidth, window.innerHeight]")
            w, h = int(w), int(h)
        except Exception:  # noqa: BLE001
            w, h = session.dimensions
        tool = {"type": "computer_20251124", "name": "computer",
                "display_width_px": w, "display_height_px": h, "display_number": 1}

        async def shot(step: int) -> tuple[str, str | None]:
            png = await page.screenshot()
            ref = session.save_screenshot_bytes(step, png)
            return base64.b64encode(png).decode(), ref

        b64, ref0 = await shot(0)
        messages: list[dict[str, Any]] = [{"role": "user", "content": [
            {"type": "text", "text": f"Task: {journey.goal}\nYou start at {journey.entry_url}. "
                                     f"The screen is {w}x{h} pixels. Here is the current screenshot."},
            {"type": "image", "source": {"type": "base64", "media_type": "image/png", "data": b64}},
        ]}]

        tokens = 0
        step = 0
        outcome = "stalled"
        final_text = ""
        while step < step_cap:
            resp = await client.beta.messages.create(
                model=self.model, max_tokens=self.max_tokens, system=SYSTEM, tools=[tool],
                messages=messages, betas=BETAS, output_config={"effort": self.effort},
                extra_body={"fallbacks": "default"},   # server-side refusal fallback (not yet a named SDK param)
            )
            u = getattr(resp, "usage", None)
            tokens += int(getattr(u, "input_tokens", 0) or 0) + int(getattr(u, "output_tokens", 0) or 0)
            if tokens > self.token_budget:
                raise RuntimeError(f"token_budget exceeded ({tokens} > {self.token_budget})")

            content = [b.model_dump(exclude_none=True) if hasattr(b, "model_dump") else b for b in resp.content]
            messages.append({"role": "assistant", "content": content})   # keep thinking blocks intact
            text = " ".join(b.get("text", "") for b in content if b.get("type") == "text").strip()
            tool_uses = [b for b in content if b.get("type") == "tool_use"]

            if resp.stop_reason == "refusal" or not tool_uses:
                final_text = text
                if COMPLETED_RE.search(text):
                    outcome = "completed"
                elif FAILED_RE.search(text) or resp.stop_reason == "refusal":
                    outcome = "stalled"
                else:
                    # Text without a marker and no action: nudge once, then treat as stalled.
                    messages.append({"role": "user", "content": [{"type": "text", "text":
                        "Continue with the computer tool, or end with TASK_COMPLETED: / TASK_FAILED:."}]})
                    step += 1
                    if step < step_cap:
                        continue
                break

            results: list[dict[str, Any]] = []
            for tu in tool_uses:
                step += 1
                inp = tu.get("input") or {}
                err = await self._do(page, inp, w, h)
                b64, ref = await shot(step)
                desc = inp.get("action", "?")
                if inp.get("coordinate"):
                    desc += f" @{tuple(inp['coordinate'])}"
                if inp.get("text"):
                    desc += f" {str(inp['text'])[:40]!r}"
                obs = page.url + (f"\n{text}" if text else "") + (f"\nerror: {err}" if err else "")
                yield ctx.event(step, desc, obs, screenshot_ref=ref)
                blocks: list[dict[str, Any]] = [{"type": "image", "source": {
                    "type": "base64", "media_type": "image/png", "data": b64}}]
                if err:
                    blocks.insert(0, {"type": "text", "text": f"Action error: {err}"})
                results.append({"type": "tool_result", "tool_use_id": tu["id"], "content": blocks,
                                **({"is_error": True} if err and "unsupported" in err else {})})
            messages.append({"role": "user", "content": results})
            self._prune_images(messages)

        b64, ref = await shot(step + 1)
        yield ctx.event(step + 1, "done", final_text or page.url, screenshot_ref=ref, outcome=outcome)  # type: ignore[arg-type]
