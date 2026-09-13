from types import SimpleNamespace

from crucible.engines.browser_use import action_name, summarise_action


def el(**kw):
    base = dict(ax_name="", attributes={}, node_name="a")
    base.update(kw)
    return SimpleNamespace(**base)


def test_click_with_accessible_name():
    a = {"click": {"index": 192}, "interacted_element": el(ax_name="Travel", node_name="A")}
    assert summarise_action(a) == "click(index='192') -> a \"Travel\""


def test_falls_back_to_attributes_then_href():
    a = {"click": {"index": 3}, "interacted_element": el(attributes={"aria-label": "Cart"}, node_name="BUTTON")}
    assert summarise_action(a).endswith('button "Cart"')
    a = {"click": {"index": 3}, "interacted_element": el(attributes={"href": "/cart"}, node_name="A")}
    assert summarise_action(a).endswith("a href=/cart")


def test_no_element():
    assert summarise_action({"scroll": {"down": 500}, "interacted_element": None}) == "scroll(down='500')"
    assert summarise_action("weird") == "weird"


def test_action_name():
    assert action_name({"interacted_element": None, "done": {"text": "x"}}) == "done"
    assert action_name(None) == ""
