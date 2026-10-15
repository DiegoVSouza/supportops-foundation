# Lockfile sync and demonstration evidence

- `uv lock --check` — exit code **0**; output: `Resolved 14 packages in 0.61ms`.
- `uv sync --locked` — exit code **0**; output: `Resolved 14 packages in 0.61ms` / `Checked 14 packages in 1ms`.
- `uv run --locked python demo/foundation_demo.py` — exit code **0**; output:

```text
customers=40 tickets=200 golden=60
dataset_sha256=8d1a2cd8823a108d450010952ec8abf5717d3c0bec2a878603418867c78b3e76
mode=fake response=Ticket received; a support specialist will review it.
```

No live LLM call occurred. Demo output is deterministic fixture behavior, not a model-quality result.
