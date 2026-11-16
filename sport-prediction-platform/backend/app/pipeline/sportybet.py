import json
import logging
from typing import List, Dict, Any, Optional
import httpx
from datetime import datetime

logger = logging.getLogger(__name__)

# Map internal league codes to Sportradar tournament URNs used by SportyBet
LEAGUE_TO_SPORTYBET_TOURNAMENT: Dict[str, str] = {
    "E0": "sr:tournament:17",      # Premier League
    "SP1": "sr:tournament:8",      # La Liga
    "I1": "sr:tournament:23",      # Serie A
    "D1": "sr:tournament:35",      # Bundesliga
    "F1": "sr:tournament:34",      # Ligue 1
    "SP2": "sr:tournament:54",     # La Liga 2 (Segunda Division)
    "E1": "sr:tournament:18",      # Championship
    "N1": "sr:tournament:37",      # Eredivisie
    "B1": "sr:tournament:38",      # Belgium Pro League
    "BR1": "sr:tournament:325"     # Brazil Serie A
}

SPORTYBET_TO_LEAGUE: Dict[str, str] = {v: k for k, v in LEAGUE_TO_SPORTYBET_TOURNAMENT.items()}

# SportyBet team name normalization map
TEAM_NAME_MAPPINGS: Dict[str, str] = {
    "Man City": "Manchester City",
    "Manchester City FC": "Manchester City",
    "Man Utd": "Manchester United",
    "Manchester United FC": "Manchester United",
    "Arsenal FC": "Arsenal",
    "Chelsea FC": "Chelsea",
    "Liverpool FC": "Liverpool",
    "Tottenham Hotspur": "Tottenham",
    "Tottenham Hotspur FC": "Tottenham",
    "Newcastle United": "Newcastle",
    "Newcastle United FC": "Newcastle",
    "Aston Villa FC": "Aston Villa",
    "Real Madrid": "Real Madrid",
    "FC Barcelona": "Barcelona",
    "Barcelona": "Barcelona",
    "Atletico Madrid": "Atletico Madrid",
    "Sevilla FC": "Sevilla",
    "Inter Milano": "Inter",
    "FC Internazionale Milano": "Inter",
    "Juventus Turin": "Juventus",
    "Juventus FC": "Juventus",
    "AC Milan": "AC Milan",
    "SSC Napoli": "Napoli",
    "Napoli": "Napoli",
    "FC Bayern Munich": "Bayern Munich",
    "Bayern Munich": "Bayern Munich",
    "Borussia Dortmund": "Dortmund",
    "Bayer 04 Leverkusen": "Bayer Leverkusen",
    "Bayer Leverkusen": "Bayer Leverkusen",
    "RB Leipzig": "RB Leipzig",
    "Paris Saint-Germain": "PSG",
    "Paris Saint-Germain FC": "PSG",
    "Olympique Marseille": "Marseille",
    "Olympique de Marseille": "Marseille"
}

def normalize_team_name(name: str) -> str:
    """Normalize team name from SportyBet to standard entity name."""
    clean = name.strip()
    return TEAM_NAME_MAPPINGS.get(clean, clean)


class SportyBetConnector:
    """Live connector for SportyBet factsCenter API."""

    BASE_URL = "https://www.sportybet.com/api/ng/factsCenter/pcEvents"

    def __init__(self, timeout: float = 6.0) -> None:
        self.timeout = timeout
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
            "Content-Type": "application/json",
            "Accept": "application/json, text/plain, */*",
            "Referer": "https://www.sportybet.com/ng/sport/football"
        }

    def parse_event(self, event: Dict[str, Any], league_id: str) -> Optional[Dict[str, Any]]:
        """Extract clean fixture and decimal odds from a SportyBet match event."""
        try:
            event_id = event.get("eventId")
            raw_home = event.get("homeTeamName", "")
            raw_away = event.get("awayTeamName", "")
            if not raw_home or not raw_away:
                return None

            home_team = normalize_team_name(raw_home)
            away_team = normalize_team_name(raw_away)

            # Match kickoff timestamp
            start_ts = event.get("estimateStartTime")
            if start_ts:
                dt = datetime.fromtimestamp(start_ts / 1000.0)
                match_date = dt.strftime("%Y-%m-%d %H:%M")
            else:
                match_date = "Upcoming"

            odds: Dict[str, float] = {
                "home": 0.0,
                "draw": 0.0,
                "away": 0.0,
                "over_2_5": 0.0,
                "under_2_5": 0.0,
                "btts_yes": 0.0,
                "btts_no": 0.0
            }

            markets = event.get("markets", [])
            for m in markets:
                m_id = str(m.get("id"))
                outcomes = m.get("outcomes", [])

                # Market 1: 1X2
                if m_id == "1":
                    for o in outcomes:
                        desc = str(o.get("desc", "")).lower()
                        val = float(o.get("odds", 0.0))
                        if desc == "home" or desc == "1":
                            odds["home"] = val
                        elif desc == "draw" or desc == "x":
                            odds["draw"] = val
                        elif desc == "away" or desc == "2":
                            odds["away"] = val

                # Market 18: Over / Under
                elif m_id == "18":
                    for o in outcomes:
                        desc = str(o.get("desc", ""))
                        val = float(o.get("odds", 0.0))
                        if "over 2.5" in desc.lower():
                            odds["over_2_5"] = val
                        elif "under 2.5" in desc.lower():
                            odds["under_2_5"] = val

                # Market 29: GG / NG (Both Teams to Score)
                elif m_id == "29":
                    for o in outcomes:
                        desc = str(o.get("desc", "")).lower()
                        val = float(o.get("odds", 0.0))
                        if desc == "yes":
                            odds["btts_yes"] = val
                        elif desc == "no":
                            odds["btts_no"] = val

            # Fill reasonable fallbacks and derived markets if secondary markets are not yet priced
            if odds["over_2_5"] <= 1.0:
                odds["over_2_5"] = 1.85
            if odds["under_2_5"] <= 1.0:
                odds["under_2_5"] = 1.95
            if odds["btts_yes"] <= 1.0:
                odds["btts_yes"] = 1.75
            if odds["btts_no"] <= 1.0:
                odds["btts_no"] = 2.05

            # Derived high-probability markets
            if odds["home"] > 1.0 and odds["draw"] > 1.0:
                inv_1x = (1.0 / odds["home"]) + (1.0 / odds["draw"])
                odds["dc_1x"] = round(1.0 / (inv_1x * 1.05), 2)
            else:
                odds["dc_1x"] = 1.35

            if odds["away"] > 1.0 and odds["draw"] > 1.0:
                inv_x2 = (1.0 / odds["away"]) + (1.0 / odds["draw"])
                odds["dc_x2"] = round(1.0 / (inv_x2 * 1.05), 2)
            else:
                odds["dc_x2"] = 1.40

            if odds["over_2_5"] > 1.0:
                odds["over_1_5"] = round(max(1.15, min(1.45, odds["over_2_5"] * 0.70)), 2)
            else:
                odds["over_1_5"] = 1.28

            return {
                "sportybet_id": event_id,
                "league_id": league_id,
                "home_team": home_team,
                "away_team": away_team,
                "match_date": match_date,
                "odds": odds
            }
        except Exception as e:
            logger.warning(f"Failed to parse SportyBet event: {e}")
            return None

    async def fetch_league_fixtures(self, league_id: str) -> List[Dict[str, Any]]:
        """Fetch live matches from SportyBet for a specific league."""
        tournament_urn = LEAGUE_TO_SPORTYBET_TOURNAMENT.get(league_id)
        if not tournament_urn:
            return []

        payload = [{
            "sportId": "sr:sport:1",
            "marketId": "1,18,29",
            "tournamentId": [[tournament_urn]]
        }]

        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                resp = await client.post(self.BASE_URL, json=payload, headers=self.headers)
                if resp.status_code == 200:
                    data = resp.json()
                    if data.get("bizCode") == 10000:
                        items = data.get("data", [])
                        parsed_fixtures = []
                        for t in items:
                            for ev in t.get("events", []):
                                pf = self.parse_event(ev, league_id)
                                if pf and pf["odds"]["home"] > 1.0:
                                    parsed_fixtures.append(pf)
                        return parsed_fixtures
        except Exception as e:
            logger.warning(f"SportyBet live fetch failed for league {league_id}: {e}")

        return []
