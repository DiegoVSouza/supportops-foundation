"""Isolated moto check: S3, SQS and SNS operations against an owned container (stdlib only)."""
import json, subprocess, sys, time, urllib.request, urllib.parse, re
from pathlib import Path

OUT = Path(__file__).parent
IMAGE = "motoserver/moto:5.2.5"
NAME = "p00-moto-046-check"
log = []

def sh(*a):
    r = subprocess.run(a, capture_output=True, text=True)
    log.append({"cmd": list(a), "exit": r.returncode, "stdout": r.stdout.strip()[-500:], "stderr": r.stderr.strip()[-500:]})
    return r

def call(url, method="GET", data=None, svc="s3"):
    h = {"Authorization": f"AWS4-HMAC-SHA256 Credential=test/20261106/us-east-1/{svc}/aws4_request, SignedHeaders=host, Signature=x"}
    if isinstance(data, bytes):
        h["Content-Type"] = "text/plain"
    if isinstance(data, dict):
        data = urllib.parse.urlencode(data).encode()
        h["Content-Type"] = "application/x-www-form-urlencoded"
    req = urllib.request.Request(url, data=data, method=method, headers=h)
    with urllib.request.urlopen(req, timeout=10) as r:
        return r.status, r.read().decode()

ok = {}
try:
    sh("docker", "rm", "-f", NAME)
    assert sh("docker", "run", "-d", "--name", NAME, "-p", "127.0.0.1::5000", IMAGE).returncode == 0
    port = re.search(r":(\d+)$", sh("docker", "port", NAME, "5000/tcp").stdout.splitlines()[0]).group(1)
    base = f"http://127.0.0.1:{port}"
    for _ in range(30):
        try:
            call(base + "/moto-api/", svc="s3"); break
        except Exception:
            time.sleep(1)
    st, _ = call(base + "/p00bucket", "PUT", b"")
    st2, _ = call(base + "/p00bucket/k.txt", "PUT", b"hello")
    _, body = call(base + "/p00bucket/k.txt")
    ok["s3_put_get"] = (st, st2, body) == (200, 200, "hello")
    _, q = call(base + "/", "POST", {"Action": "CreateQueue", "QueueName": "p00q", "Version": "2012-11-05"}, "sqs")
    qurl = re.search(r"<QueueUrl>(.*?)</QueueUrl>", q).group(1)
    call(base + "/", "POST", {"Action": "SendMessage", "QueueUrl": qurl, "MessageBody": "ping", "Version": "2012-11-05"}, "sqs")
    _, rcv = call(base + "/", "POST", {"Action": "ReceiveMessage", "QueueUrl": qurl, "Version": "2012-11-05"}, "sqs")
    ok["sqs_send_receive"] = "<Body>ping</Body>" in rcv
    _, t = call(base + "/", "POST", {"Action": "CreateTopic", "Name": "p00t", "Version": "2010-03-31"}, "sns")
    ok["sns_create_topic"] = "<TopicArn>" in t
finally:
    sh("docker", "rm", "-f", NAME)
result = {"image": IMAGE, "checks": ok, "all_passed": bool(ok) and all(ok.values()) and len(ok) == 3, "commands": log}
(OUT / "result.json").write_text(json.dumps(result, indent=2))
print(json.dumps({k: result[k] for k in ("image", "checks", "all_passed")}))
sys.exit(0 if result["all_passed"] else 1)
