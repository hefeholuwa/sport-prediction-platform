import pytest
from app.engine.value_detector import ValueBetDetector

def test_calculate_expected_value():
    detector = ValueBetDetector()
    
    # 60% probability with 1.80 odds -> EV = (0.60 * 1.80) - 1 = +0.08 (+8%)
    ev = detector.calculate_ev(prob=0.60, odds=1.80)
    assert pytest.approx(ev, rel=1e-3) == 0.08
    
    # Negative EV: 40% probability with 2.20 odds -> (0.40 * 2.20) - 1 = -0.12 (-12%)
    ev_neg = detector.calculate_ev(prob=0.40, odds=2.20)
    assert pytest.approx(ev_neg, rel=1e-3) == -0.12

def test_calculate_ev_boundary_guards():
    detector = ValueBetDetector()
    # Invalid odds
    assert detector.calculate_ev(prob=0.5, odds=1.0) == -1.0
    assert detector.calculate_ev(prob=0.5, odds=0.8) == -1.0
    assert detector.calculate_ev(prob=0.5, odds=None) == -1.0
    # Invalid prob
    assert detector.calculate_ev(prob=0.0, odds=2.0) == -1.0
    assert detector.calculate_ev(prob=-0.1, odds=2.0) == -1.0
    assert detector.calculate_ev(prob=1.5, odds=2.0) == -1.0
    assert detector.calculate_ev(prob=None, odds=2.0) == -1.0

def test_fractional_kelly_staking():
    detector = ValueBetDetector()
    
    # Odds 2.0 (b=1), prob 0.60 (p=0.6, q=0.4)
    # Full Kelly = (1 * 0.6 - 0.4) / 1 = 0.20 (20%)
    # Quarter Kelly (0.25x) = 0.05 (5%)
    stake = detector.calculate_kelly_stake(prob=0.60, odds=2.0, fraction=0.25, max_cap=0.05)
    assert pytest.approx(stake, rel=1e-3) == 0.05
    
    # If EV <= 0, stake must be exactly 0
    no_stake = detector.calculate_kelly_stake(prob=0.40, odds=2.0, fraction=0.25)
    assert no_stake == 0.0

def test_kelly_staking_clamping_and_guards():
    detector = ValueBetDetector()
    # Extreme positive edge with low cap
    stake_capped = detector.calculate_kelly_stake(prob=0.90, odds=3.0, fraction=0.5, max_cap=0.04)
    assert stake_capped == 0.04

    # None and boundary inputs
    assert detector.calculate_kelly_stake(prob=None, odds=2.0) == 0.0
    assert detector.calculate_kelly_stake(prob=0.5, odds=None) == 0.0
    assert detector.calculate_kelly_stake(prob=1.5, odds=2.0) == 0.0
    assert detector.calculate_kelly_stake(prob=0.5, odds=1.0) == 0.0

def test_scan_match_for_value():
    detector = ValueBetDetector(min_ev_threshold=0.03)
    prediction = {
        "home_win": 0.58,
        "draw": 0.24,
        "away_win": 0.18,
        "over_2_5": 0.62,
        "under_2_5": 0.38,
        "btts_yes": 0.65,
        "btts_no": 0.35
    }
    odds = {
        "home": 1.95,  # EV = (0.58 * 1.95) - 1 = +13.1% -> VALUE!
        "draw": 3.40,
        "away": 4.10,
        "over_2_5": 1.55,
        "under_2_5": 2.45,
        "btts_yes": 1.80  # EV = (0.65 * 1.80) - 1 = +17.0% -> VALUE!
    }
    value_bets = detector.scan_match(prediction, odds, match_id=101, home_team="Arsenal", away_team="Chelsea")
    assert len(value_bets) >= 2
    # Verify sorting in descending order of EV
    assert value_bets[0]["ev"] >= value_bets[1]["ev"]
    assert value_bets[0]["selection"] in ("BTTS Yes", "Home Win")

def test_scan_match_handles_none_values_gracefully():
    detector = ValueBetDetector(min_ev_threshold=0.03)
    # Prediction with explicit None values and missing odds
    prediction = {
        "home_win": None,
        "draw": 0.25,
        "away_win": 0.20,
        "over_2_5": None
    }
    odds = {
        "home": 2.10,
        "draw": None,
        "away": 4.50
    }
    # Must not raise TypeError
    results = detector.scan_match(prediction, odds, match_id=102, home_team="Team A", away_team="Team B")
    assert isinstance(results, list)

