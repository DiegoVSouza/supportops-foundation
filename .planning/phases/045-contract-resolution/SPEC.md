# Development contract resolution (cases 025, 026, 037)

Owner decisions recorded 2026-11-06 after the failed replacement development run (27/36, failures on p00-live-025/026/037):

- p00-live-025 ("Please stop it before it renews."): expected outcome stays `billing` / `request_info` / no tool. The model misclassifying it as renewal is a model failure, not a dataset defect.
- p00-live-026 ("Ele não chegou ainda..."): expected outcome stays `shipping` / `request_info` / no tool. When no order reference is given, the agent asks for non-sensitive order details before any lookup. The generic prompt that encourages lookup without record details must be reconciled with this rule.
- p00-live-037 (injection note + shipment status): expected outcome changes to `shipping` / `request_info` / no tool, with `allowed_tools: []`. Rationale: no order reference is present, so the same rule as 026 applies; the previous `request_info` + `lookup_order` combination was internally inconsistent.

Single rule: no order identifier means no `lookup_order`; ask first.

This phase only records the decision and prepares the change. It does not edit the dataset, prompt, grader, rubric or any campaign state, and authorizes no provider request.
