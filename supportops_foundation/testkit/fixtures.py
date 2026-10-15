"""Pytest fixtures are exported as plain factories so consumers can opt in."""

from supportops_foundation.testkit.dataset import SupportOpsDataset, generate_dataset


def supportops_fixture(seed: int = 7) -> SupportOpsDataset:
    return generate_dataset(seed)
