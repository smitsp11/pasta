from .base import PAYMENT_GUARD_PROMPT, Engine, RunContext  # noqa: F401


def default_engines(*, browser_use_model: str | None = None, claude_cu_model: str | None = None) -> dict:
    """Real engines, constructed lazily (imports browser_use/anthropic only when used)."""
    from .browser_use import BrowserUseEngine
    from .claude_cu import ClaudeComputerUseEngine
    engines: dict = {}
    engines["browser_use"] = BrowserUseEngine(**({"model": browser_use_model} if browser_use_model else {}))
    engines["claude_cu"] = ClaudeComputerUseEngine(**({"model": claude_cu_model} if claude_cu_model else {}))
    return engines
