from typing import List, Dict, Any, Optional
from fastapi import APIRouter, Query
from app.pipeline.sample_data import get_seed_matches
from app.engine.dixon_coles import DixonColesModel

router = APIRouter(prefix="/api", tags=["predictions"])

# Baseline empirical team ratings for Dixon-Coles engine
TEAM_RATINGS: Dict[str, Dict[str, float]] = {
    "Arsenal": {"attack": 1.45, "defense": 0.75},
    "Manchester City": {"attack": 1.60, "defense": 0.80},
    "Liverpool": {"attack": 1.55, "defense": 0.82},
    "Chelsea": {"attack": 1.25, "defense": 1.05},
    "Tottenham": {"attack": 1.30, "defense": 1.15},
    "Aston Villa": {"attack": 1.35, "defense": 1.00},
    "Newcastle": {"attack": 1.28, "defense": 1.02},
    "Manchester United": {"attack": 1.20, "defense": 1.10},
    "Real Madrid": {"attack": 1.58, "defense": 0.78},
    "Barcelona": {"attack": 1.52, "defense": 0.84},
    "Atletico Madrid": {"attack": 1.30, "defense": 0.70},
    "Sevilla": {"attack": 1.05, "defense": 1.20},
    "Inter": {"attack": 1.48, "defense": 0.72},
    "Juventus": {"attack": 1.25, "defense": 0.78},
    "AC Milan": {"attack": 1.32, "defense": 0.98},
    "Napoli": {"attack": 1.35, "defense": 0.92},
    "Bayern Munich": {"attack": 1.70, "defense": 0.85},
    "Dortmund": {"attack": 1.40, "defense": 1.08},
    "Bayer Leverkusen": {"attack": 1.50, "defense": 0.82},
    "RB Leipzig": {"attack": 1.38, "defense": 0.95},
    "PSG": {"attack": 1.65, "defense": 0.80},
    "Marseille": {"attack": 1.20, "defense": 1.05}
}

model = DixonColesModel()
model.params = TEAM_RATINGS

@router.get("/predictions", response_model=List[Dict[str, Any]])
def get_predictions(league_id: Optional[str] = Query(None)) -> List[Dict[str, Any]]:
    """Generate and return statistical Dixon-Coles predictions for upcoming matches."""
    matches = get_seed_matches()
    if league_id:
        norm_league = league_id.upper().strip()
        if norm_league != "ALL":
            matches = [m for m in matches if m["league_id"].upper() == norm_league]

    results: List[Dict[str, Any]] = []
    for idx, m in enumerate(matches):
        pred = model.predict_match(m["home_team"], m["away_team"])
        results.append({
            "id": idx + 1,
            "league_id": m["league_id"],
            "match_date": m["match_date"],
            "home_team": m["home_team"],
            "away_team": m["away_team"],
            "odds": {
                "home": m["odds_home"],
                "draw": m["odds_draw"],
                "away": m["odds_away"],
                "over_2_5": 1.85,
                "under_2_5": 1.95,
                "btts_yes": 1.75,
                "btts_no": 2.05
            },
            "prediction": pred
        })
    return results
