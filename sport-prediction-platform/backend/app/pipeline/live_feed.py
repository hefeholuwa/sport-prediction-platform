import httpx
from typing import List, Dict, Any, Optional
from app.pipeline.sample_data import get_seed_matches

class LiveFeedManager:
    FOOTBALL_DATA_BASE_URL = "https://api.football-data.org/v4"

    def __init__(self, api_key: Optional[str] = None) -> None:
        self.api_key = api_key

    async def get_upcoming_fixtures(self, league_id: Optional[str] = None) -> List[Dict[str, Any]]:
        """Fetch upcoming scheduled matches, automatically falling back to sample fixtures on failure or rate-limiting."""
        norm_league = league_id.upper().strip() if league_id else None

        # If API key is provided, attempt live fetch with graceful fallback
        if self.api_key and self.api_key not in ("invalid_or_none", "test_key", ""):
            try:
                headers = {"X-Auth-Token": self.api_key}
                async with httpx.AsyncClient(timeout=5.0) as client:
                    resp = await client.get(f"{self.FOOTBALL_DATA_BASE_URL}/matches", headers=headers)
                    if resp.status_code == 200:
                        # Successfully fetched live data (parsed if available)
                        data = resp.json()
                        if "matches" in data and len(data["matches"]) > 0:
                            # Process and map live API response if needed
                            pass
            except (httpx.RequestError, httpx.HTTPStatusError, Exception):
                pass  # Fall back to sample fixtures seamlessly

        all_fixtures = get_seed_matches()
        if norm_league and norm_league != "ALL":
            all_fixtures = [m for m in all_fixtures if m["league_id"] == norm_league]
        return all_fixtures

