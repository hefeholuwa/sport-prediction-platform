import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_api_root():
    resp = client.get("/")
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "online"
    assert "endpoints" in data

def test_api_health_and_leagues():
    resp = client.get("/api/leagues")
    assert resp.status_code == 200
    leagues = resp.json()
    assert len(leagues) >= 5
    assert any(l["id"] == "E0" for l in leagues)

def test_api_fixtures_endpoint():
    # All fixtures
    resp = client.get("/api/fixtures")
    assert resp.status_code == 200
    fixtures = resp.json()
    assert len(fixtures) >= 10
    assert "home_team" in fixtures[0]

    # Filtered by league
    resp_e0 = client.get("/api/fixtures?league_id=E0")
    assert resp_e0.status_code == 200
    fixtures_e0 = resp_e0.json()
    assert len(fixtures_e0) > 0
    assert all(f["league_id"] == "E0" for f in fixtures_e0)

def test_api_predictions_endpoint():
    resp = client.get("/api/predictions")
    assert resp.status_code == 200
    preds = resp.json()
    assert len(preds) > 0
    assert "prediction" in preds[0]
    pred_data = preds[0]["prediction"]
    assert "home_win" in pred_data
    assert "draw" in pred_data
    assert "away_win" in pred_data
    assert "matrix" in pred_data
    assert "home_xg" in pred_data
    assert "away_xg" in pred_data

    # Filtered by league
    resp_e0 = client.get("/api/predictions?league_id=E0")
    assert resp_e0.status_code == 200
    preds_e0 = resp_e0.json()
    assert len(preds_e0) > 0
    assert all(p["league_id"] == "E0" for p in preds_e0)

def test_api_value_bets_endpoint():
    resp = client.get("/api/value-bets?min_ev=0.01")
    assert resp.status_code == 200
    bets = resp.json()
    assert isinstance(bets, list)
    for b in bets:
        assert "match_id" in b
        assert "ev" in b
        assert "stake_pct" in b
        assert "kelly_stake" in b
        assert b["ev"] >= 0.01

    # Filtered by league and market
    resp_filtered = client.get("/api/value-bets?min_ev=0.01&league_id=E0&market=1X2")
    assert resp_filtered.status_code == 200
    filtered_bets = resp_filtered.json()
    assert isinstance(filtered_bets, list)
    for b in filtered_bets:
        assert b["league_id"] == "E0"
        assert b["market"] == "1X2"

    # Validation: negative min_ev should return 422
    resp_invalid = client.get("/api/value-bets?min_ev=-0.05")
    assert resp_invalid.status_code == 422

def test_api_backtest_endpoint():
    payload = {
        "league_id": "E0",
        "min_ev": 0.03,
        "staking": "flat",
        "initial_bankroll": 1000.0
    }
    resp = client.post("/api/backtest", json=payload)
    assert resp.status_code == 200
    data = resp.json()
    assert "equity_curve" in data
    assert "roi_pct" in data
    assert "total_bets" in data
    assert len(data["equity_curve"]) > 0

    # Kelly staking mode
    payload["staking"] = "kelly"
    resp_kelly = client.post("/api/backtest", json=payload)
    assert resp_kelly.status_code == 200

    # Invalid staking mode should return 422 validation error
    payload["staking"] = "invalid_mode"
    resp_invalid = client.post("/api/backtest", json=payload)
    assert resp_invalid.status_code == 422
