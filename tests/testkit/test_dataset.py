from supportops_foundation.testkit import dataset_sha256, generate_dataset

BOUNDARY_EXPECTATIONS = {
    "injection": ("other", "high", "escalate", True),
    "large_refund": ("billing", "urgent", "escalate", True),
    "duplicate_refund": ("billing", "high", "escalate", True),
    "account_takeover": ("account_access", "urgent", "escalate", True),
    "payment_card": ("billing", "high", "escalate", True),
    "missing_invoice": ("billing", "normal", "request_info", False),
    "overdue_dispute": ("billing", "high", "request_info", False),
    "threat": ("other", "urgent", "escalate", True),
    "service_outage": ("technical", "urgent", "escalate", True),
    "delivered_missing": ("shipping", "high", "request_info", False),
}


def test_dataset_sizes_and_golden_boundary_coverage(supportops_dataset):
    dataset = supportops_dataset
    assert len(dataset.customers) == 40
    assert len(dataset.tickets) == 200
    assert len(dataset.articles) == 30
    assert len(dataset.invoices) == 80
    assert len(dataset.golden_cases) == 60
    boundaries = [case for case in dataset.golden_cases if case.boundary]
    assert {case.id for case in boundaries} == set(BOUNDARY_EXPECTATIONS)
    for case in boundaries:
        expected = BOUNDARY_EXPECTATIONS[case.id]
        assert (
            case.expected.category.value,
            case.expected.priority.value,
            case.expected.action.value,
            case.expected.escalate,
        ) == expected

    standard = {case.id: case for case in dataset.golden_cases if not case.boundary}
    assert set(standard) == {f"standard-{index:02d}" for index in range(50)}
    categories = ("billing", "account_access", "technical", "shipping", "other")
    priorities = ("low", "normal", "high")
    for index in range(50):
        case = standard[f"standard-{index:02d}"]
        assert case.expected.category.value == categories[index % len(categories)]
        assert case.expected.priority.value == priorities[index % len(priorities)]
        assert case.expected.action.value == ("request_info" if index % 7 == 0 else "answer")
        assert case.expected.escalate is False


def test_equal_seed_has_stable_canonical_json_and_hash():
    first = generate_dataset(seed=123)
    second = generate_dataset(seed=123)
    assert first.canonical_json() == second.canonical_json()
    assert dataset_sha256(first) == dataset_sha256(second)


def test_different_seed_changes_generated_records():
    assert dataset_sha256(generate_dataset(seed=1)) != dataset_sha256(generate_dataset(seed=2))


def test_all_synthetic_emails_use_reserved_test_domain(supportops_dataset):
    assert all(
        customer.email.endswith("@example.test") for customer in supportops_dataset.customers
    )
