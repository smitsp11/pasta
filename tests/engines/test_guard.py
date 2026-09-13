from crucible.engines.guard import hits_payment_guard
from crucible.schemas import Config, RunEvent


def ev(action: str, observation: str = "") -> RunEvent:
    return RunEvent(run_id="r", session_id="s", journey_id="j", config=Config(), step_index=1,
                    action=action, observation=observation)


def test_payment_button_triggers():
    assert hits_payment_guard(ev('click_element_by_index(index=4, text="Place order")'))
    assert hits_payment_guard(ev('click "Pay now"'))


def test_payment_url_triggers():
    assert hits_payment_guard(ev("navigate", "https://shop.test/checkout/payment"))
    assert hits_payment_guard(ev("navigate", "https://checkout.stripe.com/c/pay/cs_123"))
    assert hits_payment_guard(ev("navigate", "https://shop.test/order/confirm?x=1"))


def test_ordinary_steps_do_not_trigger():
    assert not hits_payment_guard(ev('click "Add to cart"', "https://shop.test/products/shoe"))
    assert not hits_payment_guard(ev('click "Checkout"', "https://shop.test/cart"))
    assert not hits_payment_guard(ev("navigate", "https://shop.test/checkout"))   # reaching checkout is fine
    assert not hits_payment_guard(ev("type search 'payment plans'", "https://shop.test/search"))
