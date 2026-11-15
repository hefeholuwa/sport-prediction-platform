import pytest
import numpy as np
import pandas as pd
from app.engine.dixon_coles import DixonColesModel

def test_dixon_coles_tau_adjustment():
    model = DixonColesModel()
    assert model._tau(0, 0, 1.2, 0.8, 0.0) == 1.0
    assert model._tau(1, 0, 1.2, 0.8, 0.0) == 1.0
    
    tau_00 = model._tau(0, 0, 1.2, 0.8, -0.1)
    assert tau_00 > 1.0

def test_score_probability_matrix_sums_to_one():
    model = DixonColesModel()
    matrix = model.calculate_score_matrix(home_xg=1.85, away_xg=1.10, rho=-0.08, max_goals=7)
    
    assert matrix.shape == (7, 7)
    assert np.isclose(np.sum(matrix), 1.0, atol=1e-3)

def test_derived_market_probabilities():
    model = DixonColesModel()
    matrix = model.calculate_score_matrix(home_xg=2.1, away_xg=0.8, rho=-0.05, max_goals=7)
    probs = model.extract_market_probabilities(matrix, home_xg=2.1, away_xg=0.8)
    
    assert "home_win" in probs
    assert "draw" in probs
    assert "away_win" in probs
    assert np.isclose(probs["home_win"] + probs["draw"] + probs["away_win"], 1.0, atol=1e-2)
    assert np.isclose(probs["over_2_5"] + probs["under_2_5"], 1.0, atol=1e-2)
    assert np.isclose(probs["btts_yes"] + probs["btts_no"], 1.0, atol=1e-2)
    assert probs["home_win"] > probs["away_win"]

def test_fit_and_predict_match():
    # Mini league dataset
    matches_data = [
        {"HomeTeam": "Arsenal", "AwayTeam": "Chelsea", "FTHG": 2, "FTAG": 1, "DaysAgo": 10},
        {"HomeTeam": "Chelsea", "AwayTeam": "Liverpool", "FTHG": 1, "FTAG": 1, "DaysAgo": 20},
        {"HomeTeam": "Liverpool", "AwayTeam": "Arsenal", "FTHG": 2, "FTAG": 2, "DaysAgo": 30},
        {"HomeTeam": "Arsenal", "AwayTeam": "Liverpool", "FTHG": 3, "FTAG": 1, "DaysAgo": 40},
        {"HomeTeam": "Chelsea", "AwayTeam": "Arsenal", "FTHG": 0, "FTAG": 2, "DaysAgo": 50},
        {"HomeTeam": "Liverpool", "AwayTeam": "Chelsea", "FTHG": 1, "FTAG": 0, "DaysAgo": 60},
    ]
    df = pd.DataFrame(matches_data)
    model = DixonColesModel()
    model.fit(df)

    assert len(model.teams) == 3
    assert "Arsenal" in model.params
    assert "attack" in model.params["Arsenal"]
    assert "defense" in model.params["Arsenal"]

    # Predict an upcoming match
    prediction = model.predict_match("Arsenal", "Chelsea")
    assert "home_win" in prediction
    assert "draw" in prediction
    assert "away_win" in prediction
    assert prediction["home_win"] + prediction["draw"] + prediction["away_win"] == pytest.approx(1.0, abs=1e-2)
    assert prediction["home_xg"] > 0
    assert prediction["away_xg"] > 0

def test_predict_match_unseen_team():
    model = DixonColesModel()
    # Model with no fit still predicts using defaults safely
    pred = model.predict_match("UnknownHome", "UnknownAway")
    assert "home_win" in pred
    assert pred["home_win"] > 0.30  # Home pitch advantage baseline

def test_fit_empty_dataframe_raises():
    model = DixonColesModel()
    with pytest.raises(ValueError, match="Cannot fit model on empty DataFrame"):
        model.fit(pd.DataFrame())

