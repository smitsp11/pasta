"""Turns (category, offending element) into a concrete fix. The offending element is pulled
from the events around failure_step_index (an #id selector or quoted button/link text); if
neither is extractable, a category-specific generic noun phrase is used instead so the
sentence still names *something* concrete rather than leaving a placeholder.
"""
from __future__ import annotations

import re

from ..schemas import FailureCategory, RunResult

_ELEMENT_ID_RE = re.compile(r"#[\w-]+")
_QUOTED_TEXT_RE = re.compile(r"""['"]([^'"]{2,40})['"]""")

TEMPLATES: dict[FailureCategory, str] = {
    "cookie_wall": (
        "The {element} intercepts pointer events; make its accept control keyboard-reachable, "
        'first in DOM order, and give the dialog role="dialog" with an accessible name.'
    ),
    "captcha": (
        "A CAPTCHA on {element} blocks automated and assistive traffic alike; offer a "
        "non-visual challenge or an accessible bypass for verified agents."
    ),
    "hidden_nav": (
        "{element} is only reachable via a hover or JS-only interaction; expose it as a "
        "normal link/button in the DOM."
    ),
    "icon_only_control": (
        "{element} has no visible label; add a descriptive aria-label "
        '(e.g. aria-label="Cart") so its purpose is programmatically determinable.'
    ),
    "ambiguous_cta": (
        "{element}'s label does not describe the action it performs; rename it to a "
        "specific, task-matching label."
    ),
    "geo_block": (
        "Visitors from this country are shown a block page at {element}; if unintentional "
        "for this market, allow-list it or explain the restriction."
    ),
    "infinite_scroll": (
        "{element} loads more content only on scroll with no pagination fallback; add a "
        '"Load more" control or paginated links.'
    ),
    "login_wall": (
        "{element} requires a login before the agent can continue; allow guest access or "
        "clearly signal what's available unauthenticated."
    ),
    "layout_shift": (
        "{element} shifts after load, moving the target out from under the agent's planned "
        "click; reserve layout space for it."
    ),
    "timeout": (
        "{element} never changed after repeated actions; check for a stuck spinner, an "
        "unhandled JS error, or a redirect loop at this step."
    ),
    "other": "{element} blocked the agent; the replay at the linked step should show the specific fix needed.",
}

GENERIC_ELEMENT: dict[FailureCategory, str] = {
    "cookie_wall": "the cookie/consent overlay",
    "captcha": "the CAPTCHA challenge",
    "hidden_nav": "the navigation control the agent needed",
    "icon_only_control": "the icon-only control",
    "ambiguous_cta": "the call-to-action the agent clicked",
    "geo_block": "the page shown to this country",
    "infinite_scroll": "the content list",
    "login_wall": "the login page",
    "layout_shift": "the control that moved",
    "timeout": "the page",
    "other": "the element the agent got stuck on",
}


def offending_element(result: RunResult) -> str:
    events = result.events
    if not events:
        return ""
    pos = next((i for i, e in enumerate(events) if e.step_index == result.failure_step_index), len(events) - 1)
    window = events[max(0, pos - 2) : pos + 1]
    text = " ".join(f"{e.action} {e.observation}" for e in window)
    m = _ELEMENT_ID_RE.search(text)
    if m:
        return m.group(0)
    m = _QUOTED_TEXT_RE.search(text)
    return f'the "{m.group(1)}" element' if m else ""


def proposed_fix(category: FailureCategory, result: RunResult) -> str:
    element = offending_element(result) or GENERIC_ELEMENT.get(category, "the element the agent got stuck on")
    return TEMPLATES.get(category, TEMPLATES["other"]).format(element=element)
