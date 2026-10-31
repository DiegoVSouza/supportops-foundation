from pathlib import Path

import pytest

from supportops_foundation.testkit import generate_dataset


@pytest.fixture
def supportops_dataset():
    return generate_dataset(seed=42)


# These two modules exercise the campaign guards together with files that live in the ai-engineer-lab checkout
# (shared policies and scripts/harness). Outside the lab they cannot run, so each test is skipped with the reason
# printed by `pytest -rs`; inside the lab they run unchanged.
_LAB = Path(__file__).resolve().parents[3]
_LAB_MODULES = {"test_campaign_execution.py", "test_live_campaign_preparation.py"}
_LAB_PRESENT = (_LAB / "shared/policies/groq-free-campaign.json").is_file() and (_LAB / "scripts/harness/live_free_account.py").is_file()


def pytest_collection_modifyitems(config, items):
    if _LAB_PRESENT:
        return
    skip = pytest.mark.skip(
        reason="lab integration test: needs shared/policies and scripts/harness from the ai-engineer-lab checkout, absent here"
    )
    for item in items:
        if Path(str(item.fspath)).name in _LAB_MODULES:
            item.add_marker(skip)
