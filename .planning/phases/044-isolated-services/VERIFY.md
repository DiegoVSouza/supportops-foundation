# Verification

Status: INCOMPLETE. The isolated service attempt ran and failed at LocalStack: the configured image requires license activation. PostgreSQL vector extension/table/insert/select and Redis SET/GET succeeded. No model request occurred.

Command: `python artifacts/evidence/isolated-services-044/run.py`, cwd `projects/p00`, exit 1. Each subprocess command, exit code, stdout and stderr is saved in `artifacts/evidence/isolated-services-044/commands.json`. Startup diagnosis is in `localstack-startup.txt`. `result.json` records cleanup exit 0 and preservation of every preexisting running container. A valid LocalStack license/authentication for the pinned image is required before another service attempt; no substitute version is claimed accepted.

The initial image inventory was superseded by the recorded exact-image pull and isolated startup. Earlier execution-helper failures did not start commands and are not service gate attempts.

- [x] Confirm the dedicated Compose configuration and ownership: empty project before startup; dedicated project name and ephemeral loopback ports in compose.yml and commands.json.
- [ ] Exercise PostgreSQL, Redis and LocalStack and save command output and exit codes.
- [x] Verify cleanup of the dedicated resources and preserve the existing Docker projects: result.json, cleanup exit 0.
- [ ] Full service check remains INCOMPLETE because LocalStack cannot start without license activation. No product source changed; this phase does not repeat exhausted campaign gates.
