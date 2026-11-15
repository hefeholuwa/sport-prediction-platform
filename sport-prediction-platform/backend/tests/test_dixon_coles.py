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
