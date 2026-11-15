import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.pipeline.sportybet import SportyBetConnector, normalize_team_name

client = TestClient(app)

def test_sportybet_team_normalization():
    assert normalize_team_name("Man City") == "Manchester City"
    assert normalize_team_name("Man Utd") == "Manchester United"
    assert normalize_team_name("FC Barcelona") == "Barcelona"
    assert normalize_team_name("Paris Saint-Germain") == "PSG"
    assert normalize_team_name("Unknown Team XYZ") == "Unknown Team XYZ"

def test_sportybet_event_parser():
    connector = SportyBetConnector()
    mock_event = {
        "eventId": "sr:match:12345678",
        "homeTeamName": "Man City",
        "awayTeamName": "Arsenal FC",
        "estimateStartTime": 1795264200000,
        "markets": [
            {
                "id": "1",
                "desc": "1X2",
                "outcomes": [
                    {"desc": "Home", "odds": 1.75},
                    {"desc": "Draw", "odds": 3.80},
                    {"desc": "Away", "odds": 4.50}
                ]
            },
            {
                "id": "18",
                "desc": "Over/Under",
                "outcomes": [
                    {"desc": "Over 2.5", "odds": 1.65},
                    {"desc": "Under 2.5", "odds": 2.25}
                ]
            },
            {
                "id": "29",
                "desc": "GG/NG",
                "outcomes": [
                    {"desc": "Yes", "odds": 1.70},
                    {"desc": "No", "odds": 2.10}
                ]
            }
        ]
    }

    parsed = connector.parse_event(mock_event, league_id="E0")
    assert parsed is not None
    assert parsed["home_team"] == "Manchester City"
    assert parsed["away_team"] == "Arsenal"
    assert parsed["league_id"] == "E0"
    assert parsed["odds"]["home"] == 1.75
    assert parsed["odds"]["draw"] == 3.80
    assert parsed["odds"]["away"] == 4.50
    assert parsed["odds"]["over_2_5"] == 1.65
    assert parsed["odds"]["under_2_5"] == 2.25
    assert parsed["odds"]["btts_yes"] == 1.70
    assert parsed["odds"]["btts_no"] == 2.10

def test_api_sportybet_fixtures():
    resp = client.get("/api/sportybet/fixtures?league_id=E0")
    assert resp.status_code == 200
    fixtures = resp.json()
    assert isinstance(fixtures, list)
    assert len(fixtures) > 0
    first = fixtures[0]
    assert "sportybet_id" in first
    assert "home_team" in first
    assert "away_team" in first
    assert "odds" in first
    assert first["odds"]["home"] > 1.0

def test_api_sportybet_value_bets():
    resp = client.get("/api/sportybet/value-bets?min_ev=0.01")
    assert resp.status_code == 200
    bets = resp.json()
    assert isinstance(bets, list)
    for b in bets:
        assert "sportybet_id" in b
        assert "fixture" in b
        assert "selection" in b
        assert "bookmaker_odds" in b
        assert "ev" in b
        assert "recommended_kelly_stake" in b
        assert b["ev"] >= 0.01

def test_api_sportybet_action_sheet():
    payload = {
        "bankroll": 50000.0,
        "currency": "NGN",
        "min_ev": 0.02,
        "max_bets": 5
    }
    resp = client.post("/api/sportybet/action-sheet", json=payload)
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "ready"
    assert data["currency"] == "NGN"
    assert data["bankroll"] == 50000.0
    assert "total_allocated_stake" in data
    assert "singles" in data
    assert len(data["singles"]) > 0

    first_single = data["singles"][0]
    assert "stake_amount" in first_single
    assert "potential_return" in first_single
    assert first_single["stake_amount"] > 0
    assert first_single["currency"] == "NGN"
