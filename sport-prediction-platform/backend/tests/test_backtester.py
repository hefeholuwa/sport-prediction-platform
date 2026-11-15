import pytest
import pandas as pd
from app.engine.backtester import BacktestSimulator

def test_backtest_simulation_profit_and_metrics():
    history = [
        {"match_date": "2024-01-01", "home_team": "A", "away_team": "B", "result": "H", "odds_h": 2.0, "prob_h": 0.60}, # WON (EV +20%)
        {"match_date": "2024-01-08", "home_team": "C", "away_team": "D", "result": "D", "odds_h": 1.9, "prob_h": 0.60}, # LOST
        {"match_date": "2024-01-15", "home_team": "E", "away_team": "F", "result": "H", "odds_h": 2.2, "prob_h": 0.55}, # WON (EV +21%)
    ]
    df = pd.DataFrame(history)
    
    sim = BacktestSimulator(initial_bankroll=1000.0, min_ev=0.05, stake_mode="flat", flat_stake=50.0)
    result = sim.run(df)
    
    assert result["total_bets"] == 3
    assert result["winning_bets"] == 2
    assert result["strike_rate_pct"] == pytest.approx(66.67, rel=1e-2)
    assert result["net_profit"] > 0
    assert len(result["equity_curve"]) == 4

def test_backtest_kelly_mode():
    history = [
        {"match_date": "2024-01-01", "home_team": "A", "away_team": "B", "result": "H", "odds_h": 2.0, "prob_h": 0.60},
        {"match_date": "2024-01-08", "home_team": "C", "away_team": "D", "result": "A", "odds_h": 2.0, "prob_h": 0.60},
    ]
    df = pd.DataFrame(history)
    sim = BacktestSimulator(initial_bankroll=1000.0, min_ev=0.05, stake_mode="kelly", kelly_fraction=0.25)
    result = sim.run(df)
    assert result["total_bets"] == 2
    assert "equity_curve" in result
