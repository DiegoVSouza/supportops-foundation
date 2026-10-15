import pytest

from supportops_foundation.testkit import generate_dataset


@pytest.fixture
def supportops_dataset():
    return generate_dataset(seed=42)
