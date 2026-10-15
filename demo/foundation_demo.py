"""Run a deterministic local demonstration of the public foundation API."""

from supportops_foundation.llm import FakeClient, Message
from supportops_foundation.testkit import dataset_sha256, generate_dataset


def main() -> None:
    dataset = generate_dataset(seed=42)
    reply = FakeClient(["Ticket received; a support specialist will review it."]).complete(
        [Message("user", dataset.tickets[0].body)]
    )
    print(
        f"customers={len(dataset.customers)} tickets={len(dataset.tickets)} golden={len(dataset.golden_cases)}"
    )
    print(f"dataset_sha256={dataset_sha256(dataset)}")
    print(f"mode=fake response={reply.text}")


if __name__ == "__main__":
    main()
