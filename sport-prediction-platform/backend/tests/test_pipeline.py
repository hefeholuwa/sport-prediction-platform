import pytest
from app.pipeline.sample_data import get_seed_leagues, get_seed_matches
from app.pipeline.live_feed import LiveFeedManager

def test_seed_data_integrity():
    leagues = get_seed_leagues()
    assert len(leagues) >= 5
    league_ids = {l["id"] for l in leagues}
    assert "E0" in league_ids
    assert "SP1" in league_ids

    matches = get_seed_matches()
    assert len(matches) >= 10
    for m in matches:
        assert "home_team" in m and len(m["home_team"]) > 0
        assert "away_team" in m and len(m["away_team"]) > 0
        assert "match_date" in m
        assert m["league_id"] in league_ids
        # Validate all 3 1X2 odds are present and valid
        assert m["odds_home"] > 1.0
        assert m["odds_draw"] > 1.0
        assert m["odds_away"] > 1.0

@pytest.mark.asyncio
async def test_live_feed_graceful_fallback():
    manager = LiveFeedManager(api_key="invalid_or_none")
    # Specific league
    fixtures_e0 = await manager.get_upcoming_fixtures("E0")
    assert len(fixtures_e0) > 0
    assert all(f["league_id"] == "E0" for f in fixtures_e0)

    # Case-insensitive filtering
    fixtures_lower = await manager.get_upcoming_fixtures("e0")
    assert len(fixtures_lower) == len(fixtures_e0)

    # All leagues (None and "ALL")
    fixtures_all_none = await manager.get_upcoming_fixtures(None)
    fixtures_all_kw = await manager.get_upcoming_fixtures("ALL")
    assert len(fixtures_all_none) >= 10
    assert len(fixtures_all_none) == len(fixtures_all_kw)

    # Non-existent league returns empty list without error
    fixtures_unknown = await manager.get_upcoming_fixtures("UNKNOWN_LEAGUE")
    assert fixtures_unknown == []

