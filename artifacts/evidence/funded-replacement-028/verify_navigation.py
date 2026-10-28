"""Navigate actual private records without provider access or annotations."""
import hashlib
import http.client
import json
from pathlib import Path
import secrets
import socket
import sys
import threading
from unittest.mock import patch
from urllib.parse import quote

project = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(project))
from scripts import review_ui as ui

protected = [project / '.runtime/llm-review/answers.sqlite']
protected += sorted((project / 'artifacts/evals/live').glob('*/manifest.json'))
protected += sorted((project / 'artifacts/evals/live').glob('*/trials.jsonl'))
annotations = project / '.runtime/llm-review-ui/annotations.sqlite'
if annotations.exists():
    protected.append(annotations)
digest = lambda: {str(p.relative_to(project)): hashlib.sha256(p.read_bytes()).hexdigest() for p in protected}
before = digest()
annotation_existed = annotations.exists()
items = ui.build_review_items()
token = secrets.token_urlsafe(32)
server = ui.PrivateReviewServer(('127.0.0.1', 0), token)
thread = threading.Thread(target=server.serve_forever, daemon=True)
external = []
connect = socket.socket.connect

def local_only(sock, address):
    if address[0] != '127.0.0.1':
        external.append('denied')
        raise RuntimeError('external_connection_denied')
    return connect(sock, address)

statuses = []
try:
    thread.start()
    with patch.object(socket.socket, 'connect', local_only):
        connection = http.client.HTTPConnection('127.0.0.1', server.server_port, timeout=30)
        connection.request('GET', '/')
        response = connection.getresponse()
        assert response.status == 401
        response.read()
        connection.close()
        for path in ['/'] + ['/item/' + quote(item['item_id'], safe='') for item in items]:
            connection = http.client.HTTPConnection('127.0.0.1', server.server_port, timeout=30)
            connection.request('GET', path, headers={'Cookie': 'p00_review=' + ui._session_token(token)})
            response = connection.getresponse()
            assert response.status == 200
            assert "script-src 'none'" in response.getheader('Content-Security-Policy', '')
            response.read()
            statuses.append(response.status)
            connection.close()
finally:
    server.shutdown()
    server.server_close()
    thread.join(timeout=5)
after = digest()
assert before == after
assert annotations.exists() == annotation_existed
assert not external
report = {'status': 'PASS_NAVIGATION_ONLY', 'records': len(items),
          'authenticated_pages': len(statuses), 'unauthenticated_status': 401,
          'scripts_disabled': True, 'protected_hashes_unchanged': before == after,
          'protected_sha256': after, 'annotation_store_presence_unchanged': True,
          'annotations_written': 0, 'external_connection_attempts': len(external),
          'provider_accessed': False, 'credentials_read': False,
          'human_review': 'PENDING', 'independent_review': 'PENDING'}
print(json.dumps(report, indent=2, sort_keys=True))
