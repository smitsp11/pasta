"""Payment guard: the Runner ends a run as `completed` the moment an agent reaches payment.

Two signals, either is enough: the URL looks like a payment/confirmation page, or the last
action text looks like a purchase button. Journeys are defined to end at checkout, so
reaching it is success, and we never risk placing an order.
"""
from __future__ import annotations

import re

from ..schemas import RunEvent

PAYMENT_URL_RE = re.compile(
    r"(/pay(ment|ments)?(/|$|\?)|/checkout/(complete|confirm|payment|review)|/order/(confirm|complete|thank)|"
    r"/thank[-_]?you|/purchase/confirm|checkout\.stripe\.com|paypal\.com/checkoutnow)",
    re.IGNORECASE,
)
PAYMENT_ACTION_RE = re.compile(
    r"\b(pay now|place (your )?order|complete (purchase|order)|confirm (purchase|order|payment)|buy now|"
    r"submit (payment|order)|purchase now)\b",
    re.IGNORECASE,
)


def hits_payment_guard(ev: RunEvent) -> bool:
    text = f"{ev.action}\n{ev.observation}"
    if PAYMENT_ACTION_RE.search(ev.action or ""):
        return True
    for token in re.findall(r"https?://\S+", text):
        if PAYMENT_URL_RE.search(token):
            return True
    return False
