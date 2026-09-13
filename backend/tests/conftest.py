import pytest

import crucible.steel as steel_mod

from crucible.schemas import Journey, SiteModel
from crucible.testing import FakeSessionFactory, FakeSteelClient, no_connect, profile_ready, raw_session  # noqa: F401


@pytest.fixture
def site() -> SiteModel:
    return SiteModel(url="https://example.test", brand="Example", journeys=[
        Journey(id="find_product", name="Find a product", goal="Find any product page", entry_url="https://example.test/"),
        Journey(id="reach_checkout", name="Reach checkout", goal="Add a product and reach checkout", entry_url="https://example.test/"),
    ])


@pytest.fixture
def factory() -> FakeSessionFactory:
    return FakeSessionFactory()


@pytest.fixture(autouse=True)
def _no_credits_log(monkeypatch):
    monkeypatch.setattr(steel_mod, "CREDITS_LOG_ENABLED", False)
