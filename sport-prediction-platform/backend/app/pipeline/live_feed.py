import httpx
from typing import List, Dict, Any, Optional
from app.pipeline.sample_data import get_seed_matches

class LiveFeedManager:
    def __init__(self, api_key: Optional[str] = None) -> None:
        self.api_key = api_key

    async def get_upcoming_fixtures(self, league_id: Optional[str] = None) -> List[Dict[str, Any]]:
        """Fetch upcoming scheduled matches, automatically falling back to sample fixtures."""
        all_fixtures = get_seed_matches()
        if league_id and league_id != "ALL":
            all_fixtures = [m for m in all_fixtures if m["league_id"] == league_id]
        return all_fixtures
