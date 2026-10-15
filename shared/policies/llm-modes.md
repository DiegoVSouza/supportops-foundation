# LLM mode policy

- Test and CI default to `LLM_MODE=fake`.
- Replay uses reviewed, traceable JSONL cassettes and never accesses a provider.
- Live mode is explicit. It requires endpoint, credential, model, caller-verified rates, and a positive `LAB_MAX_USD` cap.
- The preflight reserves the configured worst-case estimate before making a request. Failed transport attempts keep their reservation because the provider may have received the request.
- Never put secrets or unredacted customer prompts in source control.
- Fake/replay outputs and synthetic adversarial fixtures are not model-quality metrics.
