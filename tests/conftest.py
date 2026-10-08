import copy
from typing import Any

import pytest
from fixtures.sample_data import data as SAMPLE


@pytest.fixture
def sample_rows() -> list[dict[str, Any]]:
    """A fresh copy per test so no test can mutate another's input."""
    return copy.deepcopy(SAMPLE)