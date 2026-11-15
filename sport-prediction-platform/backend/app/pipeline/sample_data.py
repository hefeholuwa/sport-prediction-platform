from typing import List, Dict, Any

def get_seed_leagues() -> List[Dict[str, str]]:
    return [
        {"id": "E0", "name": "Premier League", "country": "England", "csv_code": "E0"},
        {"id": "SP1", "name": "La Liga", "country": "Spain", "csv_code": "SP1"},
        {"id": "I1", "name": "Serie A", "country": "Italy", "csv_code": "I1"},
        {"id": "D1", "name": "Bundesliga", "country": "Germany", "csv_code": "D1"},
        {"id": "F1", "name": "Ligue 1", "country": "France", "csv_code": "F1"}
    ]

def get_seed_matches() -> List[Dict[str, Any]]:
    return [
        {"league_id": "E0", "match_date": "2026-11-21 15:00", "home_team": "Arsenal", "away_team": "Chelsea", "odds_home": 1.95, "odds_draw": 3.60, "odds_away": 4.10, "is_finished": False},
        {"league_id": "E0", "match_date": "2026-11-21 17:30", "home_team": "Manchester City", "away_team": "Liverpool", "odds_home": 2.10, "odds_draw": 3.75, "odds_away": 3.30, "is_finished": False},
        {"league_id": "E0", "match_date": "2026-11-22 14:00", "home_team": "Aston Villa", "away_team": "Tottenham", "odds_home": 2.35, "odds_draw": 3.50, "odds_away": 2.95, "is_finished": False},
        {"league_id": "E0", "match_date": "2026-11-22 16:30", "home_team": "Newcastle", "away_team": "Manchester United", "odds_home": 2.05, "odds_draw": 3.60, "odds_away": 3.60, "is_finished": False},
        {"league_id": "SP1", "match_date": "2026-11-21 20:00", "home_team": "Real Madrid", "away_team": "Barcelona", "odds_home": 2.15, "odds_draw": 3.65, "odds_away": 3.20, "is_finished": False},
        {"league_id": "SP1", "match_date": "2026-11-22 18:30", "home_team": "Atletico Madrid", "away_team": "Sevilla", "odds_home": 1.65, "odds_draw": 3.80, "odds_away": 5.50, "is_finished": False},
        {"league_id": "I1", "match_date": "2026-11-22 19:45", "home_team": "Inter", "away_team": "Juventus", "odds_home": 1.90, "odds_draw": 3.40, "odds_away": 4.30, "is_finished": False},
        {"league_id": "I1", "match_date": "2026-11-22 17:00", "home_team": "AC Milan", "away_team": "Napoli", "odds_home": 2.40, "odds_draw": 3.30, "odds_away": 3.00, "is_finished": False},
        {"league_id": "D1", "match_date": "2026-11-21 17:30", "home_team": "Bayern Munich", "away_team": "Dortmund", "odds_home": 1.55, "odds_draw": 4.60, "odds_away": 5.20, "is_finished": False},
        {"league_id": "D1", "match_date": "2026-11-21 14:30", "home_team": "Bayer Leverkusen", "away_team": "RB Leipzig", "odds_home": 2.05, "odds_draw": 3.70, "odds_away": 3.40, "is_finished": False},
        {"league_id": "F1", "match_date": "2026-11-22 20:00", "home_team": "PSG", "away_team": "Marseille", "odds_home": 1.45, "odds_draw": 4.80, "odds_away": 6.50, "is_finished": False}
    ]
