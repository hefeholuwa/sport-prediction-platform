import pytest
import pandas as pd
from app.engine.backtester import BacktestSimulator
from app.pipeline.historical import HistoricalDataLoader

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

def test_backtest_bankruptcy_halt():
    # 3 consecutive losses with 100% stake depletion
    history = [
        {"match_date": "2024-01-01", "home_team": "A", "away_team": "B", "result": "A", "odds_h": 2.0, "prob_h": 0.60},
        {"match_date": "2024-01-08", "home_team": "C", "away_team": "D", "result": "A", "odds_h": 2.0, "prob_h": 0.60},
        {"match_date": "2024-01-15", "home_team": "E", "away_team": "F", "result": "H", "odds_h": 2.0, "prob_h": 0.60},
    ]
    df = pd.DataFrame(history)
    sim = BacktestSimulator(initial_bankroll=100.0, min_ev=0.05, stake_mode="flat", flat_stake=100.0)
    result = sim.run(df)
    # First bet loses all $100 -> bankroll becomes 0 -> loop halts without phantom bets
    assert result["final_bankroll"] == 0.0
    assert result["total_bets"] == 1
    assert result["max_drawdown_pct"] == 100.0

def test_backtest_invalid_stake_mode_raises():
    with pytest.raises(ValueError, match="Invalid stake_mode"):
        BacktestSimulator(stake_mode="martingale")

def test_historical_data_cleaner():
    raw_data = {
        "Date": ["2024-01-01", "2024-01-08", "2024-01-15"],
        "HomeTeam": ["Arsenal", "Chelsea", "Liverpool"],
        "AwayTeam": ["Chelsea", "Liverpool", "Arsenal"],
        "FTHG": [2, None, 1], # Match 2 is unplayed
        "FTAG": [1, None, 0],
        "FTR": ["H", None, "H"],
        "B365H": [1.90, 2.10, None], # Match 3 missing B365
        "AvgH": [1.88, 2.05, 2.15],
    }
    df = pd.DataFrame(raw_data)
    cleaned = HistoricalDataLoader.clean_dataframe(df, "E0")
    # Unplayed match dropped
    assert len(cleaned) == 2
    # Match 3 uses AvgH fallback
    assert cleaned.loc[cleaned["HomeTeam"] == "Liverpool", "OddsH"].values[0] == 2.15

def test_historical_data_missing_column_raises():
    invalid_df = pd.DataFrame({"HomeTeam": ["Arsenal"]})
    with pytest.raises(ValueError, match="Missing required column"):
        HistoricalDataLoader.clean_dataframe(invalid_df, "E0")

