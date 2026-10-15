from supportops_foundation.testkit import dataset_sha256, generate_dataset


def test_dataset_sizes_and_golden_boundary_coverage(supportops_dataset):
    dataset = supportops_dataset
    assert len(dataset.customers) == 40
    assert len(dataset.tickets) == 200
    assert len(dataset.articles) == 30
    assert len(dataset.invoices) == 80
    assert len(dataset.golden_cases) == 60
    boundaries = [case for case in dataset.golden_cases if case.boundary]
    assert len(boundaries) >= 10
    assert {case.expected.category for case in dataset.golden_cases}
    assert all(case.expected.action and case.expected.priority for case in dataset.golden_cases)


def test_equal_seed_has_stable_canonical_json_and_hash():
    first = generate_dataset(seed=123)
    second = generate_dataset(seed=123)
    assert first.canonical_json() == second.canonical_json()
    assert dataset_sha256(first) == dataset_sha256(second)


def test_different_seed_changes_generated_records():
    assert dataset_sha256(generate_dataset(seed=1)) != dataset_sha256(generate_dataset(seed=2))


def test_all_synthetic_emails_use_reserved_test_domain(supportops_dataset):
    assert all(customer.email.endswith("@example.test") for customer in supportops_dataset.customers)
