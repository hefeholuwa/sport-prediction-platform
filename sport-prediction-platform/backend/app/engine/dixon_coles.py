import numpy as np
import pandas as pd
from typing import Dict, Any, List, Optional
from scipy.optimize import minimize
from scipy.stats import poisson
from app.config import MAX_GOALS_MATRIX, DEFAULT_TIME_DECAY

class DixonColesModel:
    def __init__(self, xi: float = DEFAULT_TIME_DECAY):
        self.xi: float = xi  # Time decay factor
        self.teams: List[str] = []
        self.params: Dict[str, Dict[str, float]] = {}
        self.home_advantage: float = 1.25
        self.rho: float = -0.06

    @staticmethod
    def _tau(x: int, y: int, lam: float, mu: float, rho: float) -> float:
        """Dixon-Coles adjustment factor for low-scoring matches."""
        if x == 0 and y == 0:
            return 1.0 - lam * mu * rho
        elif x == 0 and y == 1:
            return 1.0 + lam * rho
        elif x == 1 and y == 0:
            return 1.0 + mu * rho
        elif x == 1 and y == 1:
            return 1.0 - rho
        else:
            return 1.0

    def calculate_score_matrix(
        self,
        home_xg: float,
        away_xg: float,
        rho: float = -0.06,
        max_goals: int = MAX_GOALS_MATRIX
    ) -> np.ndarray:
        """Compute the 2D joint probability matrix of match scores P(X=x, Y=y)."""
        h_xg = max(0.01, float(home_xg))
        a_xg = max(0.01, float(away_xg))

        goals = np.arange(max_goals)
        p_x = poisson.pmf(goals, h_xg)
        p_y = poisson.pmf(goals, a_xg)
        matrix = np.outer(p_x, p_y)

        # Apply Dixon-Coles tau adjustment to low-scoring scorelines
        for x in (0, 1):
            for y in (0, 1):
                tau_val = max(0.0, self._tau(x, y, h_xg, a_xg, rho))
                matrix[x, y] *= tau_val

        # Normalize matrix so total probability sums to 1.0
        total_p = np.sum(matrix)
        if total_p > 0:
            matrix /= total_p
        return matrix

    def extract_market_probabilities(
        self,
        matrix: np.ndarray,
        home_xg: float,
        away_xg: float
    ) -> Dict[str, Any]:
        """Extract 1X2, Over/Under, BTTS, and most likely score from score matrix."""
        max_goals = matrix.shape[0]
        home_win_prob = float(np.sum(np.tril(matrix, -1)))
        draw_prob = float(np.sum(np.diag(matrix)))
        away_win_prob = float(np.sum(np.triu(matrix, 1)))

        # Vectorized Over / Under 2.5
        grid_x, grid_y = np.indices((max_goals, max_goals))
        over_2_5 = float(np.sum(matrix[grid_x + grid_y > 2]))
        under_2_5 = float(np.sum(matrix[grid_x + grid_y <= 2]))

        # Both Teams to Score (BTTS)
        btts_yes = float(np.sum(matrix[1:, 1:]))
        btts_no = float(1.0 - btts_yes)

        # Top 3 predicted exact scores
        flat_indices = np.argsort(matrix.ravel())[::-1]
        top_scores = []
        for idx in flat_indices[:3]:
            gx, gy = divmod(int(idx), max_goals)
            top_scores.append({
                "score": f"{gx}-{gy}",
                "probability": round(float(matrix[gx, gy]), 4)
            })

        return {
            "home_win": round(home_win_prob, 4),
            "draw": round(draw_prob, 4),
            "away_win": round(away_win_prob, 4),
            "over_2_5": round(over_2_5, 4),
            "under_2_5": round(under_2_5, 4),
            "btts_yes": round(btts_yes, 4),
            "btts_no": round(btts_no, 4),
            "home_xg": round(float(home_xg), 2),
            "away_xg": round(float(away_xg), 2),
            "predicted_score": top_scores[0]["score"],
            "top_scores": top_scores,
            "matrix": matrix.tolist()
        }

    def fit(self, df_matches: pd.DataFrame) -> None:
        """Fit attack, defense, home advantage, and rho parameters using fast vectorized MLE."""
        if df_matches.empty:
            raise ValueError("Cannot fit model on empty DataFrame")

        teams = np.sort(np.unique(np.concatenate([df_matches['HomeTeam'].values, df_matches['AwayTeam'].values])))
        self.teams = list(teams)
        n_teams = len(teams)
        team_to_id = {team: i for i, team in enumerate(teams)}

        # Pre-extract NumPy arrays for maximum vectorization performance
        h_idx = np.array([team_to_id[t] for t in df_matches['HomeTeam']], dtype=int)
        a_idx = np.array([team_to_id[t] for t in df_matches['AwayTeam']], dtype=int)
        x_vals = df_matches['FTHG'].to_numpy(dtype=int)
        y_vals = df_matches['FTAG'].to_numpy(dtype=int)

        if 'DaysAgo' in df_matches.columns:
            weights = np.exp(-self.xi * df_matches['DaysAgo'].to_numpy(dtype=float))
        else:
            weights = np.ones(len(df_matches), dtype=float)

        # Precompute low-score condition masks
        m00 = (x_vals == 0) & (y_vals == 0)
        m01 = (x_vals == 0) & (y_vals == 1)
        m10 = (x_vals == 1) & (y_vals == 0)
        m11 = (x_vals == 1) & (y_vals == 1)

        init_params = np.concatenate([
            np.ones(n_teams),
            np.ones(n_teams),
            [1.25],
            [-0.05]
        ])

        def log_likelihood(params: np.ndarray) -> float:
            att = params[:n_teams]
            defe = params[n_teams:2*n_teams]
            home_adv = params[2*n_teams]
            rho = params[2*n_teams + 1]

            penalty = 1000.0 * (np.mean(att) - 1.0) ** 2

            lam = np.maximum(0.05, att[h_idx] * defe[a_idx] * home_adv)
            mu = np.maximum(0.05, att[a_idx] * defe[h_idx])

            tau = np.ones(len(df_matches), dtype=float)
            tau[m00] = 1.0 - lam[m00] * mu[m00] * rho
            tau[m01] = 1.0 + lam[m01] * rho
            tau[m10] = 1.0 + mu[m10] * rho
            tau[m11] = 1.0 - rho
            tau = np.maximum(1e-6, tau)

            log_p = np.log(tau) + poisson.logpmf(x_vals, lam) + poisson.logpmf(y_vals, mu)
            # Safe lower bound to prevent underflow discontinuities
            ll = np.sum(weights * np.maximum(log_p, -27.63))
            return -(ll - penalty)

        bounds = [(0.1, 3.5)] * n_teams + [(0.1, 3.5)] * n_teams + [(1.0, 1.8)] + [(-0.25, 0.25)]
        res = minimize(log_likelihood, init_params, method='L-BFGS-B', bounds=bounds, options={'maxiter': 100})

        att_res = res.x[:n_teams]
        def_res = res.x[n_teams:2*n_teams]
        self.home_advantage = float(res.x[2*n_teams])
        self.rho = float(res.x[2*n_teams + 1])

        for i, team in enumerate(self.teams):
            self.params[team] = {
                "attack": float(att_res[i]),
                "defense": float(def_res[i])
            }

    def predict_match(self, home_team: str, away_team: str) -> Dict[str, Any]:
        """Predict match probabilities given two team names."""
        h_att = self.params.get(home_team, {}).get("attack", 1.0)
        h_def = self.params.get(home_team, {}).get("defense", 1.0)
        a_att = self.params.get(away_team, {}).get("attack", 1.0)
        a_def = self.params.get(away_team, {}).get("defense", 1.0)

        home_xg = max(0.2, h_att * a_def * self.home_advantage)
        away_xg = max(0.2, a_att * h_def)

        matrix = self.calculate_score_matrix(home_xg, away_xg, self.rho, max_goals=MAX_GOALS_MATRIX)
        return self.extract_market_probabilities(matrix, home_xg, away_xg)

