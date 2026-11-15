from typing import Dict, List, Any, Optional

class ValueBetDetector:
    def __init__(self, min_ev_threshold: float = 0.03, kelly_fraction: float = 0.25, max_stake_cap: float = 0.05):
        self.min_ev_threshold = min_ev_threshold
        self.kelly_fraction = kelly_fraction
        self.max_stake_cap = max_stake_cap

    @staticmethod
    def calculate_ev(prob: float, odds: float) -> float:
        """Calculate Expected Value (EV): (Probability * Decimal Odds) - 1."""
        if odds <= 1.0 or prob <= 0.0:
            return -1.0
        return (prob * odds) - 1.0

    def calculate_kelly_stake(self, prob: float, odds: float, fraction: Optional[float] = None, max_cap: Optional[float] = None) -> float:
        """Calculate Fractional Kelly stake recommendation."""
        frac = fraction if fraction is not None else self.kelly_fraction
        cap = max_cap if max_cap is not None else self.max_stake_cap

        b = odds - 1.0
        if b <= 0 or prob <= 0:
            return 0.0

        p = prob
        q = 1.0 - p
        full_kelly = (b * p - q) / b
        if full_kelly <= 0:
            return 0.0

        recommended = full_kelly * frac
        return round(min(recommended, cap), 4)

    def scan_match(self, prediction: Dict[str, Any], odds: Dict[str, float], match_id: int, home_team: str, away_team: str) -> List[Dict[str, Any]]:
        """Identify all positive EV opportunities across 1X2 and Totals markets."""
        opportunities = []

        markets_to_check = [
            ("Home Win", prediction.get("home_win", 0.0), odds.get("home", 0.0), "1X2"),
            ("Draw", prediction.get("draw", 0.0), odds.get("draw", 0.0), "1X2"),
            ("Away Win", prediction.get("away_win", 0.0), odds.get("away", 0.0), "1X2"),
            ("Over 2.5 Goals", prediction.get("over_2_5", 0.0), odds.get("over_2_5", 0.0), "Totals"),
            ("Under 2.5 Goals", prediction.get("under_2_5", 0.0), odds.get("under_2_5", 0.0), "Totals"),
            ("BTTS Yes", prediction.get("btts_yes", 0.0), odds.get("btts_yes", 0.0), "BTTS"),
            ("BTTS No", prediction.get("btts_no", 0.0), odds.get("btts_no", 0.0), "BTTS")
        ]

        for selection, prob, market_odds, market_type in markets_to_check:
            if not market_odds or market_odds <= 1.01 or prob <= 0.01:
                continue

            ev = self.calculate_ev(prob, market_odds)
            if ev >= self.min_ev_threshold:
                stake = self.calculate_kelly_stake(prob, market_odds)
                opportunities.append({
                    "match_id": match_id,
                    "fixture": f"{home_team} vs {away_team}",
                    "home_team": home_team,
                    "away_team": away_team,
                    "market": market_type,
                    "selection": selection,
                    "model_prob": round(prob, 4),
                    "model_fair_odds": round(1.0 / prob, 2) if prob > 0 else 0.0,
                    "bookmaker_odds": round(market_odds, 2),
                    "ev": round(ev, 4),
                    "ev_pct": round(ev * 100.0, 2),
                    "recommended_kelly_stake": stake,
                    "confidence": "High" if ev >= 0.08 else "Medium"
                })

        opportunities.sort(key=lambda x: x["ev"], reverse=True)
        return opportunities
