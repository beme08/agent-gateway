"""CI wrapper: the deterministic eval suite runs as part of pytest."""
from __future__ import annotations

import pytest

from app.evals.scenarios import SCENARIOS


@pytest.mark.parametrize("scenario", SCENARIOS, ids=lambda s: s.__name__)
def test_eval_scenario(scenario):
    name, checks = scenario()
    failed = [desc for desc, ok in checks if not ok]
    assert not failed, f"scenario '{name}' failed: {failed}"
