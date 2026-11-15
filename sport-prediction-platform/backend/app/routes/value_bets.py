from typing import List, Dict, Any, Optional
from fastapi import APIRouter, Query
from app.routes.predictions import get_predictions
from app.engine.value_detector import ValueBetDetector

router = APIRouter(prefix="/api", tags=["value-bets"])

@router.get("/value-bets", response_model=List[Dict[str, Any]])
def list_value_bets(
    min_ev: float = Query(0.03, ge=0.0, description="Minimum expected value threshold (e.g. 0.03 for 3%)"),
    market: Optional[str] = Query(None, description="Optional market filter (e.g. 1X2, Over/Under, BTTS)"),
    league_id: Optional[str] = Query(None, description="Optional league code filter (e.g. E0, SP1, or ALL)")
) -> List[Dict[str, Any]]:
    """Scan upcoming matches and return detected positive expected value (+EV) betting opportunities."""
    predictions = get_predictions(league_id)
    detector = ValueBetDetector(min_ev_threshold=min_ev)

    all_value_bets: List[Dict[str, Any]] = []
    for item in predictions:
        bets = detector.scan_match(
            prediction=item["prediction"],
            odds=item["odds"],
            match_id=item["id"],
            home_team=item["home_team"],
            away_team=item["away_team"]
        )
        for b in bets:
            b["league_id"] = item["league_id"]
            b["match_date"] = item["match_date"]
            b["kelly_stake"] = b["recommended_kelly_stake"]
            b["stake_pct"] = round(b["recommended_kelly_stake"] * 100.0, 2)
            all_value_bets.append(b)

    if market:
        norm_market = market.strip()
        if norm_market.upper() != "ALL":
            all_value_bets = [b for b in all_value_bets if b.get("market", "").upper() == norm_market.upper()]

    all_value_bets.sort(key=lambda x: x["ev"], reverse=True)
    return all_value_bets
