"""Record isolated service operations without touching existing Docker projects."""
import json
import pathlib
import subprocess
import time

import re, urllib.request, urllib.parse

def call(url, method="GET", data=None, svc="s3"):
    h = {"Authorization": f"AWS4-HMAC-SHA256 Credential=test/20261120/us-east-1/{svc}/aws4_request, SignedHeaders=host, Signature=x"}
    if isinstance(data, bytes):
        h["Content-Type"] = "text/plain"
    if isinstance(data, dict):
        data = urllib.parse.urlencode(data).encode()
        h["Content-Type"] = "application/x-www-form-urlencoded"
    with urllib.request.urlopen(urllib.request.Request(url, data=data, method=method, headers=h), timeout=10) as r:
        return r.status, r.read().decode()

ROOT = pathlib.Path(__file__).resolve().parent
records = []
base = ['docker', 'compose', '-p', 'p00-isolated-20261120', '-f', str(ROOT / 'compose.yml')]

def run(args):
    result = subprocess.run(args, capture_output=True, text=True, timeout=240)
    records.append(dict(command=args, cwd=str(pathlib.Path.cwd()), exit_code=result.returncode,
                        stdout=result.stdout, stderr=result.stderr))
    (ROOT / 'commands.json').write_text(json.dumps(records, indent=2), encoding='utf-8')
    return result

before = run(['docker', 'ps', '-q']).stdout.split()
assert run(base + ['ps', '-aq']).stdout.strip() == '', 'Existing owned project: stop'
ok = False
try:
    assert run(base + ['pull']).returncode == 0, 'Image acquisition failed'
    assert run(base + ['up', '-d']).returncode == 0
    for attempt in range(20):
        probe = run(base + ['exec', '-T', 'postgres', 'pg_isready', '-U', 'supportops'])
        if probe.returncode == 0:
            break
        time.sleep(2)
    assert run(base + ['exec', '-T', 'postgres', 'psql', '-U', 'supportops', '-d', 'supportops', '-v', 'ON_ERROR_STOP=1', '-c', 'CREATE EXTENSION IF NOT EXISTS vector; CREATE TEMP TABLE probe (v vector(3)); INSERT INTO probe VALUES (\' [1,2,3]\'); SELECT count(*) FROM probe;']).returncode == 0
    assert run(base + ['exec', '-T', 'redis', 'redis-cli', 'SET', 'p00-probe', 'isolated']).returncode == 0
    assert run(base + ['exec', '-T', 'redis', 'redis-cli', 'GET', 'p00-probe']).stdout.strip() == 'isolated'
    port = re.search(r":(\d+)$", run(base + ['port', 'moto', '5000']).stdout.splitlines()[0]).group(1)
    url = f"http://127.0.0.1:{port}"
    for attempt in range(30):
        try:
            call(url + "/moto-api/"); break
        except Exception:
            time.sleep(1)
    assert call(url + "/p00bucket", "PUT", b"")[0] == 200
    assert call(url + "/p00bucket/k.txt", "PUT", b"hello")[0] == 200
    assert call(url + "/p00bucket/k.txt")[1] == "hello"
    qurl = re.search(r"<QueueUrl>(.*?)</QueueUrl>", call(url + "/", "POST", {"Action": "CreateQueue", "QueueName": "p00q", "Version": "2012-11-05"}, "sqs")[1]).group(1)
    call(url + "/", "POST", {"Action": "SendMessage", "QueueUrl": qurl, "MessageBody": "ping", "Version": "2012-11-05"}, "sqs")
    assert "<Body>ping</Body>" in call(url + "/", "POST", {"Action": "ReceiveMessage", "QueueUrl": qurl, "Version": "2012-11-05"}, "sqs")[1]
    assert "<TopicArn>" in call(url + "/", "POST", {"Action": "CreateTopic", "Name": "p00t", "Version": "2010-03-31"}, "sns")[1]
    assert run(base + ['ps', '--format', 'json']).returncode == 0
    ok = True
finally:
    cleanup = run(base + ['down', '--volumes'])
    after = run(['docker', 'ps', '-q']).stdout.split()
    result = dict(service_operations_pass=ok, cleanup_exit=cleanup.returncode,
                  preexisting_running_containers_preserved=set(before).issubset(after))
    (ROOT / 'result.json').write_text(json.dumps(result, indent=2), encoding='utf-8')
    assert cleanup.returncode == 0 and result['preexisting_running_containers_preserved']
