# Replace LocalStack with moto

Owner decision 2026-11-06: replace the license-gated LocalStack image with a free, self-hosted emulator. Phase 044 failed only at LocalStack license activation. `motoserver/moto:5.2.5` (tag verified on Docker Hub, pushed 2026-10-27) covers the same S3/SQS/SNS surface with no token. No model request is authorized.
