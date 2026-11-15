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
    strategy: str = Field(default="compounder", description="'compounder' (High strike-rate 50%+ win rate) or 'value' (Pure +EV)")
    max_odds: float = Field(default=3.20, gt=1.0, description="Max decimal odds cutoff to exclude longshots")
    min_prob: float = Field(default=0.40, ge=0.0, le=1.0, description="Minimum win probability")


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
                    "over_1_5": 1.28,
                    "over_2_5": 1.85,
                    "under_2_5": 1.95,
                    "btts_yes": 1.75,
                    "btts_no": 2.05,
                    "dc_1x": 1.35,
                    "dc_x2": 1.40
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
    market: Optional[str] = Query(None, description="Market filter (e.g. 1X2, Totals, BTTS, Double Chance)"),
    league_id: Optional[str] = Query(None, description="League code filter (e.g. E0, SP1, ALL)"),
    max_odds: float = Query(3.50, gt=1.0, description="Max decimal odds cutoff to exclude longshots"),
    min_prob: float = Query(0.20, ge=0.0, description="Minimum win probability"),
    strategy: Optional[str] = Query("all", description="Strategy filter: 'compounder', 'value', or 'all'")
) -> List[Dict[str, Any]]:
    """Scan SportyBet odds with the Dixon-Coles model and return profitable +EV betting edges."""
    fixtures = await get_all_sportybet_fixtures(league_id)
    
    eff_max_odds = 2.25 if strategy == "compounder" else max_odds
    eff_min_prob = 0.48 if strategy == "compounder" else min_prob

    detector = ValueBetDetector(
        min_ev_threshold=min_ev,
        max_odds_cap=eff_max_odds,
        min_prob_threshold=eff_min_prob
    )

    value_bets: List[Dict[str, Any]] = []
    for idx, f in enumerate(fixtures):
        # Anchor predictions with bookmaker consensus for uncalibrated teams
        pred = model.predict_match(f["home_team"], f["away_team"], odds=f.get("odds"))
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

    if strategy == "compounder":
        # In compounder mode, prioritize high win probability first, then edge
        value_bets.sort(key=lambda x: (x["model_prob"], x["ev"]), reverse=True)
    else:
        value_bets.sort(key=lambda x: x["ev"], reverse=True)

    return value_bets

def build_combo_slip(
    available_bets: List[Dict[str, Any]],
    target_odds: float,
    min_leg_odds: float = 1.15,
    max_leg_odds: float = 1.85,
    min_prob: float = 0.55,
    max_legs: int = 15,
    name: str = "Combo",
    stake_amount: float = 1000.0,
    currency: str = "NGN"
) -> Optional[Dict[str, Any]]:
    """Construct an optimal non-correlated accumulator slip targeting a specific combined odds payout."""
    # Deduplicate: exactly 1 selection per fixture to ensure valid betslip
    fixture_best: Dict[str, Dict[str, Any]] = {}
    for b in available_bets:
        f = b["fixture"]
        if f not in fixture_best:
            fixture_best[f] = b
        else:
            if b["model_prob"] > fixture_best[f]["model_prob"]:
                fixture_best[f] = b

    candidates = list(fixture_best.values())
    if not candidates:
        return None

    # Filter pool by preferred odds and probability
    pool = [c for c in candidates if min_leg_odds <= c["bookmaker_odds"] <= max_leg_odds and c["model_prob"] >= min_prob]
    if len(pool) < 2:
        pool = [c for c in candidates if c["bookmaker_odds"] <= 2.25]

    pool.sort(key=lambda x: (x["model_prob"], x.get("ev", 0.0)), reverse=True)

    selected_legs = []
    combined_odds = 1.0
    combined_prob = 1.0
    used_fixtures = set()

    for leg in pool:
        if leg["fixture"] in used_fixtures:
            continue

        selected_legs.append(leg)
        used_fixtures.add(leg["fixture"])
        combined_odds *= leg["bookmaker_odds"]
        combined_prob *= leg["model_prob"]

        if combined_odds >= target_odds * 0.90 or len(selected_legs) >= max_legs:
            break

    if len(selected_legs) < 2 or combined_odds < target_odds * 0.60:
        return None

    return {
        "name": name,
        "target_odds": round(target_odds, 2),
        "combined_odds": round(combined_odds, 2),
        "combined_win_prob_pct": round(combined_prob * 100.0, 1),
        "legs_count": len(selected_legs),
        "stake_amount": round(stake_amount, 2),
        "currency": currency,
        "potential_return": round(stake_amount * combined_odds, 2),
        "legs": [
            {
                "fixture": l["fixture"],
                "selection": l["selection"],
                "market": l.get("market", "1X2"),
                "sportybet_odds": l["bookmaker_odds"],
                "prob_pct": round(l["model_prob"] * 100.0, 1),
                "sportybet_id": l.get("sportybet_id")
            }
            for l in selected_legs
        ]
    }


@router.post("/action-sheet", response_model=Dict[str, Any])
async def generate_action_sheet(req: ActionSheetRequest) -> Dict[str, Any]:
    """Generate a daily actionable betslip on SportyBet (singles + 2, 5, 10, 50, 100 odds combos)."""
    # Fetch all value bets meeting min_ev and strategy criteria
    raw_bets = await list_sportybet_value_bets(
        min_ev=req.min_ev,
        market="ALL",
        league_id="ALL",
        max_odds=req.max_odds,
        min_prob=req.min_prob,
        strategy=req.strategy
    )

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

    # Build Multi-Tier Acca Combos (2 Sure Odds, 5 Odds, 10 Odds, 50 Odds, 100 Odds)
    combo_2 = build_combo_slip(raw_bets, 2.0, min_leg_odds=1.20, max_leg_odds=1.65, min_prob=0.65, max_legs=3, name="2 Sure Odds Banker", stake_amount=round(req.bankroll * 0.03, 2), currency=req.currency)
    combo_5 = build_combo_slip(raw_bets, 5.0, min_leg_odds=1.25, max_leg_odds=1.75, min_prob=0.60, max_legs=5, name="5 Sure Odds Multiplier", stake_amount=round(req.bankroll * 0.015, 2), currency=req.currency)
    combo_10 = build_combo_slip(raw_bets, 10.0, min_leg_odds=1.30, max_leg_odds=1.80, min_prob=0.58, max_legs=8, name="10 Odds Value Ticket", stake_amount=round(req.bankroll * 0.008, 2), currency=req.currency)
    combo_50 = build_combo_slip(raw_bets, 50.0, min_leg_odds=1.35, max_leg_odds=1.95, min_prob=0.52, max_legs=11, name="50 Mega Odds Ticket", stake_amount=max(100.0, round(req.bankroll * 0.003, 2)), currency=req.currency)
    combo_100 = build_combo_slip(raw_bets, 100.0, min_leg_odds=1.35, max_leg_odds=2.05, min_prob=0.50, max_legs=14, name="100 Mega Odds Jackpot", stake_amount=max(100.0, round(req.bankroll * 0.002, 2)), currency=req.currency)

    combos = {
        "two_odds": combo_2,
        "five_odds": combo_5,
        "ten_odds": combo_10,
        "fifty_odds": combo_50,
        "hundred_odds": combo_100
    }

    conservative_double = combo_2

    return {
        "status": "ready",
        "strategy": req.strategy,
        "bankroll": req.bankroll,
        "currency": req.currency,
        "total_allocated_stake": round(total_allocated_stake, 2),
        "portfolio_allocation_pct": round((total_allocated_stake / req.bankroll) * 100.0, 2),
        "singles": singles,
        "conservative_double": conservative_double,
        "combos": combos,
        "timestamp": "Today"
    }


@router.get("/combos", response_model=Dict[str, Any])
async def get_sportybet_combos(
    bankroll: float = Query(50000.0, gt=0),
    currency: str = Query("NGN"),
    min_ev: float = Query(0.01, ge=0.0)
) -> Dict[str, Any]:
    """Generate all popular combo slips (2 Odds, 5 Odds, 10 Odds, 50 Odds, 100 Odds)."""
    raw_bets = await list_sportybet_value_bets(
        min_ev=min_ev,
        market="ALL",
        league_id="ALL",
        strategy="compounder"
    )
    combo_2 = build_combo_slip(raw_bets, 2.0, min_leg_odds=1.20, max_leg_odds=1.65, min_prob=0.65, max_legs=3, name="2 Sure Odds Banker", stake_amount=round(bankroll * 0.03, 2), currency=currency)
    combo_5 = build_combo_slip(raw_bets, 5.0, min_leg_odds=1.25, max_leg_odds=1.75, min_prob=0.60, max_legs=5, name="5 Sure Odds Multiplier", stake_amount=round(bankroll * 0.015, 2), currency=currency)
    combo_10 = build_combo_slip(raw_bets, 10.0, min_leg_odds=1.30, max_leg_odds=1.80, min_prob=0.58, max_legs=8, name="10 Odds Value Ticket", stake_amount=round(bankroll * 0.008, 2), currency=currency)
    combo_50 = build_combo_slip(raw_bets, 50.0, min_leg_odds=1.35, max_leg_odds=1.95, min_prob=0.52, max_legs=11, name="50 Mega Odds Ticket", stake_amount=max(100.0, round(bankroll * 0.003, 2)), currency=currency)
    combo_100 = build_combo_slip(raw_bets, 100.0, min_leg_odds=1.35, max_leg_odds=2.05, min_prob=0.50, max_legs=14, name="100 Mega Odds Jackpot", stake_amount=max(100.0, round(bankroll * 0.002, 2)), currency=currency)

    return {
        "status": "ready",
        "bankroll": bankroll,
        "currency": currency,
        "combos": {
            "two_odds": combo_2,
            "five_odds": combo_5,
            "ten_odds": combo_10,
            "fifty_odds": combo_50,
            "hundred_odds": combo_100
        }
    }

