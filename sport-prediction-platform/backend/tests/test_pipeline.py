import pytest
from app.pipeline.sample_data import get_seed_leagues, get_seed_matches
from app.pipeline.live_feed import LiveFeedManager

def test_seed_data_integrity():
    leagues = get_seed_leagues()
    assert len(leagues) >= 5
    assert any(l["id"] == "E0" for l in leagues)

    matches = get_seed_matches()
    assert len(matches) >= 10
    for m in matches:
        assert "home_team" in m
        assert "away_team" in m
        assert "odds_home" in m
        assert m["odds_home"] > 1.0

@pytest.mark.asyncio
async def test_live_feed_graceful_fallback():
    manager = LiveFeedManager(api_key="invalid_or_none")
    fixtures = await manager.get_upcoming_fixtures("E0")
    assert len(fixtures) > 0
    assert fixtures[0]["home_team"] != ""
