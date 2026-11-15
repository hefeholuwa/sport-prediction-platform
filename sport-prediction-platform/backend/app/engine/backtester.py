from typing import Dict, List, Any
import pandas as pd
import numpy as np

class BacktestSimulator:
    def __init__(
        self,
        initial_bankroll: float = 1000.0,
        min_ev: float = 0.04,
        stake_mode: str = "flat",
        flat_stake: float = 20.0,
        kelly_fraction: float = 0.20
    ) -> None:
        self.initial_bankroll = float(initial_bankroll)
        self.min_ev = float(min_ev)
        self.stake_mode = stake_mode  # "flat" or "kelly"
        self.flat_stake = float(flat_stake)
        self.kelly_fraction = float(kelly_fraction)

    def run(self, df_matches: pd.DataFrame) -> Dict[str, Any]:
        """Simulate betting history against historical closing odds."""
        bankroll = self.initial_bankroll
        equity_curve = [{"step": 0, "date": "Start", "bankroll": round(bankroll, 2), "pnl": 0.0}]
        
        total_bets = 0
        winning_bets = 0
        total_staked = 0.0
        peak_bankroll = bankroll
        max_drawdown = 0.0

        for idx, row in df_matches.iterrows():
            prob_h = row.get("prob_h")
            odds_h = row.get("odds_h")
            result = row.get("result", "")
            date_str = str(row.get("match_date", f"Match {idx+1}"))

            if prob_h is None or odds_h is None:
                continue
            if odds_h <= 1.01 or prob_h <= 0.0 or prob_h > 1.0:
                continue

            ev = (prob_h * odds_h) - 1.0
            if ev >= self.min_ev:
                total_bets += 1

                # Determine stake size
                if self.stake_mode == "kelly":
                    b = odds_h - 1.0
                    f_star = (b * prob_h - (1.0 - prob_h)) / b
                    stake = round(max(0.0, min(0.05, f_star * self.kelly_fraction)) * bankroll, 2)
                    if stake < 5.0 and bankroll >= 5.0:
                        stake = 5.0
                else:
                    stake = min(bankroll, self.flat_stake)

                stake = min(stake, bankroll)
                if stake <= 0:
                    continue

                total_staked += stake

                if result == "H":
                    winning_bets += 1
                    profit = (odds_h - 1.0) * stake
                    bankroll += profit
                else:
                    bankroll -= stake

                # Update max drawdown
                peak_bankroll = max(peak_bankroll, bankroll)
                dd = (peak_bankroll - bankroll) / peak_bankroll if peak_bankroll > 0 else 0.0
                max_drawdown = max(max_drawdown, dd)

                equity_curve.append({
                    "step": total_bets,
                    "date": date_str,
                    "bankroll": round(bankroll, 2),
                    "pnl": round(bankroll - self.initial_bankroll, 2)
                })

        net_profit = bankroll - self.initial_bankroll
        roi_pct = (net_profit / total_staked * 100.0) if total_staked > 0 else 0.0
        strike_rate = (winning_bets / total_bets * 100.0) if total_bets > 0 else 0.0

        return {
            "initial_bankroll": self.initial_bankroll,
            "final_bankroll": round(bankroll, 2),
            "net_profit": round(net_profit, 2),
            "roi_pct": round(roi_pct, 2),
            "total_bets": total_bets,
            "winning_bets": winning_bets,
            "strike_rate_pct": round(strike_rate, 2),
            "max_drawdown_pct": round(max_drawdown * 100.0, 2),
            "equity_curve": equity_curve
        }
