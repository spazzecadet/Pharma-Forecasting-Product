import sys
from pathlib import Path

# Ensure we can import the API when running from repo root
repo_root = Path(__file__).resolve().parents[1]
api_path = repo_root / 'services' / 'api'
if str(api_path) not in sys.path:
    sys.path.insert(0, str(api_path))

from fastapi.testclient import TestClient
from main import app


def test_health_ok():
    client = TestClient(app)
    r = client.get('/health')
    assert r.status_code == 200
    assert r.json().get('status') == 'ok'

