# Local P00 package provenance

- Package: `supportops-foundation==1.0.0`
- Source commit: `e48c6ac3d7047c20d6e68b17ee36e1a1b1b0347d`
- Build command: `uv build --offline --out-dir artifacts/packages`
- Build exit code: **0**. Full output: `package-build.txt`.
- Wheel: `artifacts/packages/supportops_foundation-1.0.0-py3-none-any.whl`
- Wheel SHA-256: `0CB839A42E5834DFB7E5368DAE06BF0C57B3266EE4E04346B60F3E5A1650806C`
- Source archive: `artifacts/packages/supportops_foundation-1.0.0.tar.gz`
- Source archive SHA-256: `0E5BE7ACA322EEF0AEB06243B30D5E0BB40245BD200D6F4C1822E28250A0925D`
- Isolated wheel install: `uv pip install --target artifacts/tmp/wheel-install --no-deps artifacts/packages/supportops_foundation-1.0.0-py3-none-any.whl` — exit code **0**.
- Isolated smoke: from `artifacts/tmp`, run `..\..\.venv\Scripts\python.exe -c "import sys; sys.path.insert(0, 'wheel-install'); import supportops_foundation as p; from supportops_foundation.testkit import generate_dataset; from supportops_foundation.llm import get_llm, Message; d=generate_dataset(42); r=get_llm().complete([Message('user','smoke')]); print(f'version={p.__version__} customers={len(d.customers)} tickets={len(d.tickets)} mode={r.provider}')"` — exit code **0**; output: `version=1.0.0 customers=40 tickets=200 mode=fake`.

This wheel is a local integration artifact only. It was not published to an external registry. Provider quality, cost, and latency remain **PENDING**.
