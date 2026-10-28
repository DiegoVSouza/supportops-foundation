"""Read-only local review probe; never print or persist response bodies or tokens."""

import hashlib
import http.client
import json
import secrets
import sys
import threading
from collections import Counter
from pathlib import Path
from urllib.parse import quote

ROOT = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(ROOT))
from scripts import review_ui


def snapshot():
    paths = [ROOT / ".runtime/llm-review/answers.sqlite"]
    for name in ("free-pilot-v1", "free-dev-c1", "free-dev-c2"):
        paths.extend((ROOT / "artifacts/evals/live" / name).glob("*"))
    return {str(p): hashlib.sha256(p.read_bytes()).hexdigest() for p in paths if p.is_file()}


before = snapshot()
items = review_ui.build_review_items()
token = secrets.token_urlsafe(32)
server = review_ui.PrivateReviewServer(("127.0.0.1", 0), token)
worker = threading.Thread(target=server.serve_forever, daemon=True)
worker.start()
checks = {}
try:
    connection = http.client.HTTPConnection("127.0.0.1", server.server_port, timeout=30)
    connection.request("GET", "/")
    response = connection.getresponse()
    checks["unauthenticated_status"] = response.status
    response.read()
    connection.request("POST", "/login", "token=invalid")
    response = connection.getresponse()
    checks["invalid_token_status"] = response.status
    response.read()
    connection.request("POST", "/login", "token=" + token)
    response = connection.getresponse()
    cookie = response.getheader("Set-Cookie").split(";", 1)[0]
    checks["login_status"] = response.status
    response.read()
    headers = {"Cookie": cookie}
    connection.request("GET", "/", headers=headers)
    response = connection.getresponse()
    checks["index_status"] = response.status
    checks["scripts_disabled"] = "script-src 'none'" in response.getheader("Content-Security-Policy")
    response.read()
    statuses = []
    for item in items:
        connection.request("GET", "/item/" + quote(item["item_id"], safe=""), headers=headers)
        response = connection.getresponse()
        statuses.append(response.status)
        response.read()
    checks["item_statuses_all_200"] = all(status == 200 for status in statuses)
    connection.close()
finally:
    server.shutdown()
    server.server_close()
    worker.join(timeout=30)
assert before == snapshot(), "Historical/private answer files changed"
assert checks["unauthenticated_status"] == checks["invalid_token_status"] == 401
assert checks["login_status"] == checks["index_status"] == 200
assert checks["item_statuses_all_200"] and checks["scripts_disabled"]
report = {
    "checks": checks,
    "items": len(items),
    "response_counts": dict(Counter(item["campaign_id"] for item in items if item["response_available"])),
    "records_without_response": sum(not item["response_available"] for item in items),
    "historical_and_private_answer_files_unchanged": True,
    "provider_accessed": False,
    "credentials_read": False,
    "annotations_written": 0,
    "human_review": "PENDING",
    "independent_review": "PENDING",
}
print(json.dumps(report, indent=2))
