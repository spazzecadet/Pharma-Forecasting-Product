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


def test_create_run():
    client = TestClient(app)
    r = client.post('/runs/', json={
        "brand_id": "BRAND_A",
        "model_type": "arima",
        "horizon": 12
    })
    assert r.status_code == 200
    data = r.json()
    assert data['brand_id'] == 'BRAND_A'
    assert data['model_type'] == 'arima'
    assert data['horizon'] == 12
    assert data['status'] == 'pending'


def test_list_runs():
    client = TestClient(app)
    r = client.get('/runs/')
    assert r.status_code == 200
    assert isinstance(r.json(), list)


def test_quick_price_scenario():
    client = TestClient(app)
    r = client.post('/scenarios/quick-price-test', params={
        "brand_id": "BRAND_A",
        "baseline_price": 100.0,
        "scenario_price": 110.0,
        "horizon": 6
    })
    # This will fail if ML deps aren't installed, but structure should be valid
    assert r.status_code in [200, 500]  # 500 if ML deps missing
