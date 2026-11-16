from typing import List, Dict, Any, Optional
from fastapi import APIRouter, Query
from app.pipeline.sample_data import get_seed_matches
from app.engine.dixon_coles import DixonColesModel

router = APIRouter(prefix="/api", tags=["predictions"])

# Baseline empirical team ratings for Dixon-Coles engine across Top 5 European Leagues
TEAM_RATINGS: Dict[str, Dict[str, float]] = {
    # Premier League
    "Arsenal": {"attack": 1.50, "defense": 0.72},
    "Manchester City": {"attack": 1.65, "defense": 0.78},
    "Liverpool": {"attack": 1.60, "defense": 0.80},
    "Chelsea": {"attack": 1.35, "defense": 1.00},
    "Tottenham": {"attack": 1.32, "defense": 1.10},
    "Aston Villa": {"attack": 1.36, "defense": 0.98},
    "Newcastle": {"attack": 1.30, "defense": 1.00},
    "Manchester United": {"attack": 1.22, "defense": 1.08},
    "Brighton": {"attack": 1.25, "defense": 1.12},
    "West Ham": {"attack": 1.15, "defense": 1.18},
    "Brentford": {"attack": 1.20, "defense": 1.16},
    "Fulham": {"attack": 1.15, "defense": 1.12},
    "Bournemouth": {"attack": 1.18, "defense": 1.15},
    "Everton": {"attack": 0.95, "defense": 1.10},
    "Crystal Palace": {"attack": 1.02, "defense": 1.12},
    "Wolves": {"attack": 1.00, "defense": 1.25},
    "Nottingham Forest": {"attack": 1.05, "defense": 1.05},
    "Leicester": {"attack": 0.98, "defense": 1.30},
    "Southampton": {"attack": 0.90, "defense": 1.40},
    "Ipswich": {"attack": 0.88, "defense": 1.45},

    # La Liga
    "Real Madrid": {"attack": 1.65, "defense": 0.72},
    "Barcelona": {"attack": 1.68, "defense": 0.82},
    "Atletico Madrid": {"attack": 1.35, "defense": 0.68},
    "Athletic Club": {"attack": 1.28, "defense": 0.82},
    "Girona": {"attack": 1.25, "defense": 1.10},
    "Real Sociedad": {"attack": 1.10, "defense": 0.85},
    "Real Betis": {"attack": 1.15, "defense": 0.98},
    "Villarreal": {"attack": 1.38, "defense": 1.18},
    "Osasuna": {"attack": 1.05, "defense": 1.08},
    "Mallorca": {"attack": 0.92, "defense": 0.90},
    "Celta Vigo": {"attack": 1.18, "defense": 1.22},
    "Rayo Vallecano": {"attack": 0.98, "defense": 1.05},
    "Sevilla": {"attack": 1.08, "defense": 1.15},
    "Alaves": {"attack": 0.95, "defense": 1.15},
    "Las Palmas": {"attack": 0.92, "defense": 1.25},
    "Getafe": {"attack": 0.82, "defense": 0.95},
    "Espanyol": {"attack": 0.90, "defense": 1.28},
    "Leganes": {"attack": 0.85, "defense": 1.15},
    "Valencia": {"attack": 0.92, "defense": 1.22},
    "Real Valladolid": {"attack": 0.80, "defense": 1.40},

    # Serie A
    "Inter": {"attack": 1.55, "defense": 0.70},
    "Juventus": {"attack": 1.28, "defense": 0.65},
    "Atalanta": {"attack": 1.55, "defense": 0.92},
    "Napoli": {"attack": 1.38, "defense": 0.78},
    "Lazio": {"attack": 1.35, "defense": 0.98},
    "Fiorentina": {"attack": 1.30, "defense": 0.92},
    "AC Milan": {"attack": 1.38, "defense": 0.98},
    "Roma": {"attack": 1.25, "defense": 0.95},
    "Bologna": {"attack": 1.20, "defense": 0.95},
    "Torino": {"attack": 1.02, "defense": 1.08},
    "Udinese": {"attack": 1.05, "defense": 1.12},
    "Empoli": {"attack": 0.88, "defense": 0.98},
    "Parma": {"attack": 1.05, "defense": 1.30},
    "Genoa": {"attack": 0.90, "defense": 1.18},
    "Como": {"attack": 1.00, "defense": 1.22},
    "Cagliari": {"attack": 0.95, "defense": 1.28},
    "Verona": {"attack": 0.98, "defense": 1.35},
    "Lecce": {"attack": 0.82, "defense": 1.25},
    "Monza": {"attack": 0.85, "defense": 1.18},
    "Venezia": {"attack": 0.85, "defense": 1.35},

    # Bundesliga
    "Bayern Munich": {"attack": 1.85, "defense": 0.75},
    "Bayer Leverkusen": {"attack": 1.62, "defense": 0.85},
    "Dortmund": {"attack": 1.50, "defense": 1.05},
    "RB Leipzig": {"attack": 1.42, "defense": 0.88},
    "Eintracht Frankfurt": {"attack": 1.48, "defense": 1.10},
    "Stuttgart": {"attack": 1.40, "defense": 1.05},
    "Freiburg": {"attack": 1.18, "defense": 1.05},
    "Borussia Monchengladbach": {"attack": 1.20, "defense": 1.18},
    "Mainz": {"attack": 1.15, "defense": 1.08},
    "Werder Bremen": {"attack": 1.18, "defense": 1.22},
    "Augsburg": {"attack": 1.10, "defense": 1.25},
    "Wolfsburg": {"attack": 1.12, "defense": 1.20},
    "Union Berlin": {"attack": 0.95, "defense": 1.02},
    "Hoffenheim": {"attack": 1.22, "defense": 1.35},
    "St. Pauli": {"attack": 0.88, "defense": 1.15},
    "Heidenheim": {"attack": 1.05, "defense": 1.28},
    "FC Koln": {"attack": 0.90, "defense": 1.35},
    "Cologne": {"attack": 0.90, "defense": 1.35},
    "Hamburger SV": {"attack": 0.92, "defense": 1.38},
    "Bochum": {"attack": 0.88, "defense": 1.45},
    "Holstein Kiel": {"attack": 0.88, "defense": 1.50},

    # Ligue 1
    "PSG": {"attack": 1.75, "defense": 0.75},
    "Monaco": {"attack": 1.45, "defense": 0.90},
    "Marseille": {"attack": 1.42, "defense": 0.95},
    "Lille": {"attack": 1.30, "defense": 0.85},
    "Lyon": {"attack": 1.35, "defense": 1.05},
    "Lens": {"attack": 1.15, "defense": 0.88},
    "Nice": {"attack": 1.18, "defense": 0.85},
    "Rennes": {"attack": 1.15, "defense": 1.10},
    "Brest": {"attack": 1.18, "defense": 1.05},
    "Reims": {"attack": 1.10, "defense": 1.08},
    "Toulouse": {"attack": 1.02, "defense": 1.08},
    "Strasbourg": {"attack": 1.15, "defense": 1.20},
    "Auxerre": {"attack": 1.05, "defense": 1.18},
    "Nantes": {"attack": 0.95, "defense": 1.12},
    "Angers": {"attack": 0.90, "defense": 1.15},
    "Montpellier": {"attack": 0.95, "defense": 1.35},
    "Saint-Etienne": {"attack": 0.88, "defense": 1.40},
    "Le Havre": {"attack": 0.82, "defense": 1.25}
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
