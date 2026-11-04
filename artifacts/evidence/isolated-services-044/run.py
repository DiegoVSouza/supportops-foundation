"""Record isolated service operations without touching existing Docker projects."""
import json
import pathlib
import subprocess
import time

ROOT = pathlib.Path(__file__).resolve().parent
records = []
base = ['docker', 'compose', '-p', 'p00-isolated-044', '-f', str(ROOT / 'compose.yml')]

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
    for attempt in range(20):
        queue = run(base + ['exec', '-T', 'localstack', 'awslocal', 'sqs', 'create-queue', '--queue-name', 'p00-probe'])
        if queue.returncode == 0:
            break
        time.sleep(2)
    assert queue.returncode == 0
    assert run(base + ['exec', '-T', 'localstack', 'awslocal', 'sqs', 'list-queues']).returncode == 0
    assert run(base + ['ps', '--format', 'json']).returncode == 0
    ok = True
finally:
    cleanup = run(base + ['down', '--volumes'])
    after = run(['docker', 'ps', '-q']).stdout.split()
    result = dict(service_operations_pass=ok, cleanup_exit=cleanup.returncode,
                  preexisting_running_containers_preserved=set(before).issubset(after))
    (ROOT / 'result.json').write_text(json.dumps(result, indent=2), encoding='utf-8')
    assert cleanup.returncode == 0 and result['preexisting_running_containers_preserved']
