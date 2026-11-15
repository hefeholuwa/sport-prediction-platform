from typing import List, Dict, Any, Optional
from fastapi import APIRouter, Query
from pydantic import BaseModel, Field
from app.pipeline.sportybet import SportyBetConnector, LEAGUE_TO_SPORTYBET_TOURNAMENT
from app.routes.predictions import model
from app.engine.value_detector import ValueBetDetector
from app.pipeline.sample_data import get_seed_matches

router = APIRouter(prefix="/api/sportybet", tags=["sportybet"])

connector = SportyBetConnector()

class ActionSheetRequest(BaseModel):
    bankroll: float = Field(default=50000.0, gt=0, description="Total bankroll amount (e.g. ₦50,000)")
    currency: str = Field(default="NGN", description="Currency symbol/code (e.g. NGN, USD, GBP)")
    min_ev: float = Field(default=0.03, ge=0.0, description="Minimum edge threshold (e.g. 0.03 for 3%)")
    max_bets: int = Field(default=5, ge=1, le=20, description="Maximum number of singles in action sheet")


async def get_all_sportybet_fixtures(league_id: Optional[str] = None) -> List[Dict[str, Any]]:
    """Fetch live SportyBet fixtures across leagues with graceful fallback."""
    target_leagues = [league_id.upper()] if league_id and league_id.upper() != "ALL" else list(LEAGUE_TO_SPORTYBET_TOURNAMENT.keys())
    
    all_fixtures = []
    for l_id in target_leagues:
        live_matches = await connector.fetch_league_fixtures(l_id)
        if live_matches:
            all_fixtures.extend(live_matches)

    # Fallback to sample data if SportyBet feed is temporarily unreachable
    if not all_fixtures:
        seed = get_seed_matches()
        if league_id and league_id.upper() != "ALL":
            seed = [m for m in seed if m["league_id"].upper() == league_id.upper()]
        for idx, m in enumerate(seed):
            all_fixtures.append({
                "sportybet_id": f"sr:match:fallback_{idx + 1}",
                "league_id": m["league_id"],
                "home_team": m["home_team"],
                "away_team": m["away_team"],
                "match_date": m["match_date"],
                "odds": {
                    "home": m["odds_home"],
                    "draw": m["odds_draw"],
                    "away": m["odds_away"],
                    "over_2_5": 1.85,
                    "under_2_5": 1.95,
                    "btts_yes": 1.75,
                    "btts_no": 2.05
                }
            })

    return all_fixtures


@router.get("/fixtures", response_model=List[Dict[str, Any]])
async def list_sportybet_fixtures(league_id: Optional[str] = Query(None)) -> List[Dict[str, Any]]:
    """Return live scheduled matches and decimal odds from SportyBet."""
    return await get_all_sportybet_fixtures(league_id)


@router.get("/value-bets", response_model=List[Dict[str, Any]])
async def list_sportybet_value_bets(
    min_ev: float = Query(0.03, ge=0.0, description="Minimum EV threshold"),
    market: Optional[str] = Query(None, description="Market filter (e.g. 1X2, Totals, BTTS)"),
    league_id: Optional[str] = Query(None, description="League code filter (e.g. E0, SP1, ALL)")
) -> List[Dict[str, Any]]:
    """Scan SportyBet odds with the Dixon-Coles model and return profitable +EV betting edges."""
    fixtures = await get_all_sportybet_fixtures(league_id)
    detector = ValueBetDetector(min_ev_threshold=min_ev)

    value_bets: List[Dict[str, Any]] = []
    for idx, f in enumerate(fixtures):
        pred = model.predict_match(f["home_team"], f["away_team"])
        bets = detector.scan_match(
            prediction=pred,
            odds=f["odds"],
            match_id=idx + 1,
            home_team=f["home_team"],
            away_team=f["away_team"]
        )
        for b in bets:
            b["sportybet_id"] = f.get("sportybet_id", f"sr:match:{idx + 1}")
            b["league_id"] = f["league_id"]
            b["match_date"] = f["match_date"]
            b["kelly_stake"] = b["recommended_kelly_stake"]
            b["stake_pct"] = round(b["recommended_kelly_stake"] * 100.0, 2)
            value_bets.append(b)

    if market and market.upper() != "ALL":
        value_bets = [b for b in value_bets if b.get("market", "").upper() == market.strip().upper()]

    value_bets.sort(key=lambda x: x["ev"], reverse=True)
    return value_bets


@router.post("/action-sheet", response_model=Dict[str, Any])
async def generate_action_sheet(req: ActionSheetRequest) -> Dict[str, Any]:
    """Generate a daily actionable betslip on SportyBet (singles + conservative accumulator)."""
    # Fetch all value bets meeting min_ev
    raw_bets = await list_sportybet_value_bets(min_ev=req.min_ev, market="ALL", league_id="ALL")

    singles = []
    total_allocated_stake = 0.0

    for b in raw_bets[:req.max_bets]:
        stake_amount = round(req.bankroll * b["recommended_kelly_stake"], 2)
        total_allocated_stake += stake_amount
        singles.append({
            "fixture": b["fixture"],
            "sportybet_id": b.get("sportybet_id"),
            "market": b["market"],
            "selection": b["selection"],
            "sportybet_odds": b["bookmaker_odds"],
            "model_prob_pct": round(b["model_prob"] * 100.0, 1),
            "ev_pct": b["ev_pct"],
            "recommended_stake_pct": b["stake_pct"],
            "stake_amount": stake_amount,
            "currency": req.currency,
            "potential_return": round(stake_amount * b["bookmaker_odds"], 2)
        })

    # Build Conservative 2-Leg Accumulator from top 2 highest probability +EV bets
    conservative_double = None
    high_prob_bets = sorted(raw_bets, key=lambda x: x["model_prob"], reverse=True)
    if len(high_prob_bets) >= 2:
        leg1 = high_prob_bets[0]
        # Ensure leg 2 is from a different fixture to avoid correlation issues
        leg2 = next((b for b in high_prob_bets[1:] if b["fixture"] != leg1["fixture"]), None)
        if leg2:
            combined_odds = round(leg1["bookmaker_odds"] * leg2["bookmaker_odds"], 2)
            combined_prob = leg1["model_prob"] * leg2["model_prob"]
            double_stake = round(req.bankroll * 0.02, 2)  # Conservative 2% stake
            total_allocated_stake += double_stake
            conservative_double = {
                "name": "Daily Value Double",
                "legs": [
                    {
                        "fixture": leg1["fixture"],
                        "selection": leg1["selection"],
                        "sportybet_odds": leg1["bookmaker_odds"],
                        "prob_pct": round(leg1["model_prob"] * 100.0, 1)
                    },
                    {
                        "fixture": leg2["fixture"],
                        "selection": leg2["selection"],
                        "sportybet_odds": leg2["bookmaker_odds"],
                        "prob_pct": round(leg2["model_prob"] * 100.0, 1)
                    }
                ],
                "combined_odds": combined_odds,
                "combined_win_prob_pct": round(combined_prob * 100.0, 1),
                "stake_amount": double_stake,
                "currency": req.currency,
                "potential_return": round(double_stake * combined_odds, 2)
            }

    return {
        "status": "ready",
        "bankroll": req.bankroll,
        "currency": req.currency,
        "total_allocated_stake": round(total_allocated_stake, 2),
        "portfolio_allocation_pct": round((total_allocated_stake / req.bankroll) * 100.0, 2),
        "singles": singles,
        "conservative_double": conservative_double,
        "timestamp": "Today"
    }
