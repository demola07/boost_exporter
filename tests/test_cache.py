from boost_exporter import ExportCache


class FakeClock:
    """A clock the test moves forward by hand, so expiry needs no sleeping."""

    def __init__(self) -> None:
        self.now = 0.0

    def __call__(self) -> float:
        return self.now


def test_get_returns_none_for_a_missing_key() -> None:
    assert ExportCache().get("missing") is None


def test_entry_is_served_until_the_ttl_elapses() -> None:
    clock = FakeClock()
    cache = ExportCache(clock=clock)
    cache.set("key", "data")

    clock.now = 3599.0
    assert cache.get("key") == "data"

    clock.now = 3600.0
    assert cache.get("key") is None


def test_set_replaces_the_value_and_restarts_the_ttl() -> None:
    clock = FakeClock()
    cache = ExportCache(clock=clock)
    cache.set("key", "old")

    clock.now = 3000.0
    cache.set("key", "new")

    clock.now = 4000.0  # past the first entry's hour, within the second's
    assert cache.get("key") == "new"
