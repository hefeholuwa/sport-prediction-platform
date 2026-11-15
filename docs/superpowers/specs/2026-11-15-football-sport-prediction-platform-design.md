# Football Match Prediction & Value Betting Platform — System Design Document

**Date:** 2026-11-15  
**Status:** Approved  
**Author:** AI System Architect & User  
**Target Architecture:** Python FastAPI + React / Vite + Tailwind CSS + SQLite  

---

## 1. Executive Summary & Objectives

The goal is to build an automated, mathematically rigorous **Football (Soccer) Match Prediction and Value Betting Platform**. 

Instead of relying on black-box heuristics or subjective opinions, the platform uses an established quantitative sports analytics framework: the **Dixon-Coles Bivariate Poisson Model** with exponential time-decay weighting. It produces joint scoreline probability matrices ($P(X=x, Y=y)$), which derive exact fair probabilities for all major betting markets:
1. **1X2 (Match Outcome)**: Home Win, Draw, Away Win.
2. **Over / Under 2.5 Goals**: Total expected match goals.
3. **Both Teams to Score (BTTS)**: Yes / No.
4. **Expected Goals ($xG$) & Most Likely Exact Scores**.

The platform couples these probabilities with live bookmaker odds to automatically detect **Positive Expected Value (+EV) bets**, calculate optimal fractional Kelly stake recommendations, and provide an interactive **Historical Backtesting Engine** to empirically verify model performance and return on investment (ROI).

---

## 2. System Architecture

```text
+-----------------------------------------------------------------------------------+
|                                  CLIENT LAYER                                     |
|                       React 18 + Vite + Tailwind CSS + Lucide                     |
|  [Match Predictions View]  [Value Bet Scanner]  [Backtest Lab]  [Match Deep Dive] |
+------------------------------------------+----------------------------------------+
                                           | HTTP / REST (JSON)
                                           v
+-----------------------------------------------------------------------------------+
|                                FASTAPI BACKEND                                    |
|  - CORS & Middleware                     - SQLite ORM Models                      |
|  - Pydantic Schemas                      - Rate Limit & Cache Controller          |
+---------------------+--------------------+--------------------+-------------------+
                      |                    |                    |
                      v                    v                    v
+----------------------------+ +----------------------+ +---------------------------+
|      DATA PIPELINE         | |  STATISTICAL ENGINE  | |      VALUE & BACKTEST     |
| - football-data.co.uk CSVs | | - Dixon-Coles Poisson| | - Expected Value (EV)     |
| - Football-Data.org API    | | - Time Decay Decay   | | - Kelly Criterion Staking |
| - The-Odds-API Client      | | - Attack/Defense     | | - Historical Backtester   |
| - Offline Mock Fallback    | | - 7x7 Score Heatmap  | | - Brier Score & ROI calc  |
+----------------------------+ +----------------------+ +---------------------------+
                                           |
                                           v
+-----------------------------------------------------------------------------------+
|                               PERSISTENCE LAYER                                   |
|                     SQLite Database (sports_predictions.db)                       |
|           Tables: leagues, teams, matches, closing_odds, predictions              |
+-----------------------------------------------------------------------------------+
```

---

## 3. Directory Structure

```text
sport-prediction-platform/
├── backend/
│   ├── app/
│   │   ├── __init__.py
│   │   ├── main.py              # FastAPI app creation, CORS, router mounting
│   │   ├── config.py            # League codes, API URLs, constants
│   │   ├── database.py          # SQLAlchemy SQLite connection & sessions
│   │   ├── models/              # Database models (League, Team, Match, Prediction)
│   │   │   ├── __init__.py
│   │   │   └── schema.py
│   │   ├── engine/              # Quantitative math & prediction core
│   │   │   ├── __init__.py
│   │   │   ├── dixon_coles.py   # Dixon-Coles solver & score matrix generator
│   │   │   ├── value_detector.py# EV calculator & fractional Kelly staking
│   │   │   └── backtester.py    # Historical backtester & simulation engine
│   │   ├── pipeline/            # Ingestion & external feed connectors
│   │   │   ├── __init__.py
│   │   │   ├── historical.py    # football-data.co.uk CSV parser
│   │   │   ├── live_feed.py     # Football-Data.org & The-Odds-API client
│   │   │   └── sample_data.py   # Realistic fallback fixtures & odds
│   │   └── routes/              # API endpoints
│   │       ├── __init__.py
│   │       ├── fixtures.py      # /api/fixtures, /api/leagues
│   │       ├── predictions.py   # /api/predictions
│   │       ├── value_bets.py    # /api/value-bets
│   │       └── backtest.py      # /api/backtest
│   ├── requirements.txt
│   └── tests/
│       ├── test_dixon_coles.py
│       ├── test_value_detector.py
│       ├── test_backtester.py
│       └── test_api.py
├── frontend/
│   ├── index.html
│   ├── package.json
│   ├── vite.config.js
│   ├── tailwind.config.js
│   ├── postcss.config.js
│   └── src/
│       ├── main.jsx
│       ├── App.jsx
│       ├── index.css
│       ├── components/
│       │   ├── Navbar.jsx
│       │   ├── LeagueSelector.jsx
│       │   ├── MatchCard.jsx
│       │   ├── ValueBetScanner.jsx
│       │   ├── BacktestVisualizer.jsx
│       │   ├── MatchModal.jsx
│       │   └── StatBadge.jsx
│       └── services/
│           └── api.js
└── docs/
    └── superpowers/specs/2026-11-15-football-sport-prediction-platform-design.md
```

---

## 4. Mathematical Modeling & Quantitative Strategy

### 4.1 Dixon-Coles Bivariate Poisson Model
Standard Poisson assumes goals scored by home and away teams are independent. In practice, football games have low scores ($0\text{-}0, 1\text{-}0, 0\text{-}1, 1\text{-}1$) with negative correlation due to game state tactics.

1. **Parameters**:
   * For each team $i$:
     * Attack strength $\alpha_i > 0$
     * Defense weakness $\beta_i > 0$
   * Global home field advantage $\gamma > 0$
   * Identifiability constraint: $\frac{1}{N} \sum_{i=1}^N \alpha_i = 1$
   * Expected goals:
     $$\lambda_k = \alpha_{\text{home}} \cdot \beta_{\text{away}} \cdot \gamma$$
     $$\mu_k = \alpha_{\text{away}} \cdot \beta_{\text{home}}$$

2. **Time Decay Weighting**:
   * Weight each historical match $k$ played $t_k$ days ago:
     $$w(t_k) = \exp(-\xi \cdot t_k)$$
     where $\xi = 0.003$ (half-life of approximately 230 days).

3. **Low-Score Interaction Parameter $\tau(\cdot)$**:
   * For home goals $x$ and away goals $y$:
     $$\tau(x, y) = \begin{cases}
     1 - \lambda \mu \rho & x=0, y=0 \\
     1 + \mu \rho & x=0, y=1 \\
     1 + \lambda \rho & x=1, y=0 \\
     1 - \rho & x=1, y=1 \\
     1 & \text{otherwise}
     \end{cases}$$
   * Joint probability of score $(x, y)$:
     $$P(X=x, Y=y) = \tau(x, y) \cdot \frac{\lambda^x e^{-\lambda}}{x!} \cdot \frac{\mu^y e^{-\mu}}{y!}$$

4. **Derivative Markets**:
   * 1X2 Probabilities:
     $$P(\text{Home Win}) = \sum_{x > y} P(x, y), \quad P(\text{Draw}) = \sum_{x = y} P(x, y), \quad P(\text{Away Win}) = \sum_{x < y} P(x, y)$$
   * Over 2.5 Goals: $P(\text{Over 2.5}) = \sum_{x + y > 2} P(x, y)$
   * Both Teams to Score: $P(\text{BTTS}) = \sum_{x \ge 1, y \ge 1} P(x, y)$

### 4.2 Value Bet Detection
* Given bookmaker decimal odds $O$:
* Implied bookmaker probability: $P_{\text{bookmaker}} = \frac{1}{O}$
* Expected Value (EV):
  $$\text{EV} = (P_{\text{model}} \times O) - 1$$
* Any bet with $\text{EV} \ge +0.03$ (+3%) is marked as a positive edge; $\text{EV} \ge +0.05$ is flagged as high confidence.

### 4.3 Staking: Fractional Kelly Criterion
* Full Kelly percentage:
  $$f^* = \frac{b \cdot p - (1 - p)}{b} \quad \text{where } b = O - 1, \, p = P_{\text{model}}$$
* To protect bankroll from drawdown variance, the system computes:
  $$\text{Stake} = \max\left(0, \min(0.05, 0.25 \times f^*)\right) \times \text{Bankroll}$$
  (Capped at a maximum of 5% of bankroll per bet).

---

## 5. Data Flow & External API Strategy

### 5.1 Historical Matches
* Downloaded directly from `https://www.football-data.co.uk/mmz4281/{season}/{league}.csv`.
* Supported leagues:
  * `E0`: English Premier League
  * `SP1`: Spanish La Liga
  * `I1`: Italian Serie A
  * `D1`: German Bundesliga
  * `F1`: French Ligue 1
* Extracted fields: Date, HomeTeam, AwayTeam, FTHG (Full Time Home Goals), FTAG, FTR (Result), HS (Home Shots), AS, HST (Shots on Target), AST, B365H, B365D, B365A (Bet365 closing odds), MaxH, MaxD, MaxA (Pinnacle/Market consensus odds).

### 5.2 Upcoming Fixtures & Odds
* Fixtures: Synced via Football-Data.org API (`/v4/competitions/{id}/matches?status=SCHEDULED`).
* Odds: Synced via The-Odds-API (`/v4/sports/soccer_{league}/odds/?regions=eu&markets=h2h,totals`).
* **Resilience Mechanism**: When API keys are unconfigured or when HTTP 429 rate limits are encountered, the system activates `sample_data.py` fixtures with authentic odds. This ensures 100% testability with zero setup barriers.

---

## 6. Database Schema (SQLite)

```sql
CREATE TABLE leagues (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    country TEXT NOT NULL,
    csv_code TEXT NOT NULL
);

CREATE TABLE teams (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL UNIQUE,
    league_id TEXT NOT NULL REFERENCES leagues(id),
    attack_rating REAL DEFAULT 1.0,
    defense_rating REAL DEFAULT 1.0,
    updated_at TIMESTAMP
);

CREATE TABLE matches (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    league_id TEXT NOT NULL REFERENCES leagues(id),
    match_date DATE NOT NULL,
    home_team TEXT NOT NULL,
    away_team TEXT NOT NULL,
    home_goals INTEGER,
    away_goals INTEGER,
    result TEXT, -- 'H', 'D', 'A'
    odds_home REAL,
    odds_draw REAL,
    odds_away REAL,
    is_finished BOOLEAN DEFAULT 0
);

CREATE TABLE predictions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    match_id INTEGER NOT NULL REFERENCES matches(id),
    home_win_prob REAL NOT NULL,
    draw_prob REAL NOT NULL,
    away_win_prob REAL NOT NULL,
    over_2_5_prob REAL NOT NULL,
    under_2_5_prob REAL NOT NULL,
    btts_yes_prob REAL NOT NULL,
    btts_no_prob REAL NOT NULL,
    home_xg REAL NOT NULL,
    away_xg REAL NOT NULL,
    predicted_score TEXT NOT NULL, -- e.g. "2-1"
    score_matrix_json TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

---

## 7. Backend REST API Contract

1. `GET /api/leagues`
   * Returns list of supported competitions with match counts.
2. `GET /api/fixtures`
   * Query params: `league_id` (optional), `status` ('scheduled' | 'finished'), `limit`.
   * Returns matches with joined model predictions and latest odds.
3. `GET /api/predictions`
   * Query params: `league_id`, `date`.
   * Returns structured predictions with probability breakdowns.
4. `GET /api/value-bets`
   * Query params: `min_ev` (default: 0.03), `market` ('1X2' | 'totals' | 'btts').
   * Returns sorted list of high-edge bets with Kelly stakes.
5. `POST /api/backtest`
   * Request body: `{ "league_id": "E0", "min_ev": 0.05, "market": "1X2", "staking": "kelly" | "flat", "initial_bankroll": 1000.0 }`
   * Returns summary: `{ "total_bets": 142, "win_rate": 0.54, "final_bankroll": 1284.50, "roi_pct": 28.45, "max_drawdown_pct": 8.2, "equity_curve": [...] }`
6. `POST /api/pipeline/sync`
   * Triggers historical ingestion and recalculates Dixon-Coles parameters.

---

## 8. Frontend User Experience & Components

* **Dark Theme**: Modern sports analytics visual styling (`#0B0F19` background, `#1E293B` card surfaces, `#10B981` positive value accents, `#F59E0B` caution accents).
* **Views**:
  1. **Predictions Dashboard**: Visual cards with probability dials, xG projected scoreline, Over/Under & BTTS pills.
  2. **Value Bet Scanner**: Fast interactive data table filterable by minimum EV percentage and market.
  3. **Backtest Laboratory**: Interactive simulator with equity curve chart showing performance against closing odds.
  4. **Deep Dive Modal**: $7 \times 7$ score probability heatmap matrix, team attack/defense ratings, and recent form.

---

## 9. Error Handling & Edge Cases

1. **API Rate Limiting**: Cached in SQLite with a 30-minute TTL for odds and 6-hour TTL for fixtures. Fallback to sample data on 429 errors.
2. **Numerical Instability**: Parameter optimization uses L-BFGS-B with bounds $\alpha_i, \beta_i \in [0.05, 5.0]$ and $\gamma \in [0.8, 1.8]$. Dirichlet priors prevent singularities for new teams.
3. **Probability Calibration**: All joint probabilities are normalized so $\sum_{x=0}^6 \sum_{y=0}^6 P(x, y) = 1.0$.

---

## 10. Verification & Quality Gates

* **Unit Tests**:
  * Dixon-Coles mathematical convergence and matrix probability sum = 1.0.
  * Expected value formulas and Kelly staking bounded within safe risk thresholds.
  * Backtesting equity calculation correctness.
* **Integration Tests**:
  * FastAPI endpoints return 200 OK with correct schema.
  * Frontend builds cleanly with zero JSX/Vite errors (`npm run build`).
