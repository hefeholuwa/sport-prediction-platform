import numpy as np
import pandas as pd
from scipy.optimize import minimize
from scipy.stats import poisson
from app.config import MAX_GOALS_MATRIX, DEFAULT_TIME_DECAY

class DixonColesModel:
    def __init__(self, xi=DEFAULT_TIME_DECAY):
        self.xi = xi  # Time decay factor
        self.teams = []
        self.params = {}
        self.home_advantage = 1.25
        self.rho = -0.06

    @staticmethod
    def _tau(x, y, lam, mu, rho):
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

    def calculate_score_matrix(self, home_xg: float, away_xg: float, rho: float = -0.06, max_goals: int = MAX_GOALS_MATRIX) -> np.ndarray:
        """Compute the 2D joint probability matrix of match scores P(X=x, Y=y)."""
        matrix = np.zeros((max_goals, max_goals))
        for x in range(max_goals):
            for y in range(max_goals):
                p_x = poisson.pmf(x, home_xg)
                p_y = poisson.pmf(y, away_xg)
                tau_val = max(0.0, self._tau(x, y, home_xg, away_xg, rho))
                matrix[x, y] = tau_val * p_x * p_y

        total_p = np.sum(matrix)
        if total_p > 0:
            matrix /= total_p
        return matrix

    def extract_market_probabilities(self, matrix: np.ndarray, home_xg: float, away_xg: float) -> dict:
        """Extract 1X2, Over/Under, BTTS, and most likely score from score matrix."""
        max_goals = matrix.shape[0]
        home_win_prob = float(np.sum(np.tril(matrix, -1)))
        draw_prob = float(np.sum(np.diag(matrix)))
        away_win_prob = float(np.sum(np.triu(matrix, 1)))

        # Over / Under 2.5
        over_2_5 = 0.0
        under_2_5 = 0.0
        for x in range(max_goals):
            for y in range(max_goals):
                if x + y > 2:
                    over_2_5 += matrix[x, y]
                else:
                    under_2_5 += matrix[x, y]

        # Both Teams to Score (BTTS)
        btts_yes = float(np.sum(matrix[1:, 1:]))
        btts_no = 1.0 - btts_yes

        # Top 3 predicted exact scores
        flat_indices = np.argsort(matrix.ravel())[::-1]
        top_scores = []
        for idx in flat_indices[:3]:
            gx, gy = divmod(idx, max_goals)
            top_scores.append({
                "score": f"{gx}-{gy}",
                "probability": round(float(matrix[gx, gy]), 4)
            })

        return {
            "home_win": round(home_win_prob, 4),
            "draw": round(draw_prob, 4),
            "away_win": round(away_win_prob, 4),
            "over_2_5": round(float(over_2_5), 4),
            "under_2_5": round(float(under_2_5), 4),
            "btts_yes": round(btts_yes, 4),
            "btts_no": round(float(btts_no), 4),
            "home_xg": round(float(home_xg), 2),
            "away_xg": round(float(away_xg), 2),
            "predicted_score": top_scores[0]["score"],
            "top_scores": top_scores,
            "matrix": matrix.tolist()
        }

    def fit(self, df_matches: pd.DataFrame):
        """Fit attack, defense, home advantage, and rho parameters using MLE."""
        teams = np.sort(np.unique(np.concatenate([df_matches['HomeTeam'].values, df_matches['AwayTeam'].values])))
        self.teams = list(teams)
        n_teams = len(teams)
        team_to_id = {team: i for i, team in enumerate(teams)}

        init_params = np.concatenate([
            np.ones(n_teams),
            np.ones(n_teams),
            [1.25],
            [-0.05]
        ])

        def log_likelihood(params):
            att = params[:n_teams]
            defe = params[n_teams:2*n_teams]
            home_adv = params[2*n_teams]
            rho = params[2*n_teams + 1]

            penalty = 1000.0 * (np.mean(att) - 1.0) ** 2

            ll = 0.0
            for _, row in df_matches.iterrows():
                h_idx = team_to_id[row['HomeTeam']]
                a_idx = team_to_id[row['AwayTeam']]
                x = int(row['FTHG'])
                y = int(row['FTAG'])

                lam = max(0.05, att[h_idx] * defe[a_idx] * home_adv)
                mu = max(0.05, att[a_idx] * defe[h_idx])

                tau_val = max(1e-6, self._tau(x, y, lam, mu, rho))
                p_match = tau_val * poisson.pmf(x, lam) * poisson.pmf(y, mu)
                if p_match > 1e-12:
                    w = 1.0
                    if 'DaysAgo' in row:
                        w = np.exp(-self.xi * row['DaysAgo'])
                    ll += w * np.log(p_match)

            return -(ll - penalty)

        bounds = [(0.1, 3.5)] * n_teams + [(0.1, 3.5)] * n_teams + [(1.0, 1.8)] + [(-0.25, 0.25)]
        res = minimize(log_likelihood, init_params, method='L-BFGS-B', bounds=bounds, options={'maxiter': 50})
        
        att_res = res.x[:n_teams]
        def_res = res.x[n_teams:2*n_teams]
        self.home_advantage = float(res.x[2*n_teams])
        self.rho = float(res.x[2*n_teams + 1])

        for i, team in enumerate(self.teams):
            self.params[team] = {
                "attack": float(att_res[i]),
                "defense": float(def_res[i])
            }

    def predict_match(self, home_team: str, away_team: str) -> dict:
        """Predict match probabilities given two team names."""
        h_att = self.params.get(home_team, {}).get("attack", 1.0)
        h_def = self.params.get(home_team, {}).get("defense", 1.0)
        a_att = self.params.get(away_team, {}).get("attack", 1.0)
        a_def = self.params.get(away_team, {}).get("defense", 1.0)

        home_xg = max(0.2, h_att * a_def * self.home_advantage)
        away_xg = max(0.2, a_att * h_def)

        matrix = self.calculate_score_matrix(home_xg, away_xg, self.rho, max_goals=MAX_GOALS_MATRIX)
        return self.extract_market_probabilities(matrix, home_xg, away_xg)
