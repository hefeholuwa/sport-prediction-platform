# ApexPredict: Quantitative Football Prediction & +EV Betting Platform

ApexPredict is a full-stack quantitative soccer forecasting and positive expected value (+EV) betting platform. It leverages the classical **Dixon-Coles (1997) Bivariate Poisson Model** with exponential time-decay weighting, fair market price estimation, fractional Kelly criterion bankroll management, and an interactive historical strategy backtesting engine.

---

## ⚡ Key Capabilities

1. **Dixon-Coles Bivariate Poisson Engine (`backend/app/engine/dixon_coles.py`)**:
   - Vectorized Maximum Likelihood Estimation (MLE) via `scipy.optimize.minimize` (`L-BFGS-B`).
   - Attack, defense, and home-advantage latent parameters per team with attack normalization constraint $\frac{1}{N}\sum \alpha_i = 1.0$.
   - Low-score correlation adjustment factor ($\tau(x, y)$) with dependency parameter $\rho$.
   - Exponential time-decay match weighting $w_k = \exp(-\xi \cdot \Delta t)$ ($\xi = 0.0065$).
   - Computes complete $7 \times 7$ score probability matrices ($P(X=x, Y=y)$), extracting 1X2 match probabilities, Over/Under 2.5, Both Teams to Score (BTTS), and Expected Goals ($xG$).

2. **Positive Expected Value (+EV) Detector (`backend/app/engine/value_detector.py`)**:
   - Calculates exact mathematical edge: $\text{EV} = (P_{\text{model}} \times \text{Odds}_{\text{bookmaker}}) - 1.0$.
   - Sizing via Fractional Kelly Criterion: $f^* = \frac{b \cdot p - q}{b}$ scaled by $c = 0.25$ (Quarter-Kelly) with hard cap at 5% of bankroll.

3. **Historical Strategy Backtester (`backend/app/engine/backtester.py`)**:
   - Simulates betting strategy over historical match sequences.
   - Computes ROI %, Net Profit/Loss, Strike Rate, Maximum Drawdown %, and step-by-step Bankroll Equity Curve.
   - Halts automatically upon bankroll depletion to prevent phantom betting.

4. **Modular FastAPI REST API (`backend/app/routes/`)**:
   - `GET /api/leagues`: Returns supported European football competitions.
   - `GET /api/fixtures`: Returns upcoming matches with optional `league_id` filter.
   - `GET /api/predictions`: Computes Dixon-Coles probability distributions and xG.
   - `GET /api/value-bets`: Scans matches for +EV opportunities with `min_ev`, `market`, and `league_id` filters.
   - `POST /api/backtest`: Executes historical strategy simulations with parameter validation.

5. **Modern React / Vite / Tailwind UI (`frontend/`)**:
   - Tri-color 1X2 probability distribution gauges and animated `+EV EDGE` alerts.
   - Interactive Dixon-Coles $7 \times 7$ Scoreline Matrix Heatmap modal.
   - Dynamic Value Bet Scanner table with one-click edge cutoffs and market filtering.
   - Interactive Backtest Lab with customizable bankroll and dynamic visual equity curve.

---

## 🚀 Quickstart & Setup

### Prerequisites
- Python 3.10+ (tested on Python 3.14 on Linux ARM64 / Termux)
- Node.js 18+ and npm

### 1. Launch Backend API
```bash
cd sport-prediction-platform
./run_backend.sh
```
*Backend runs on `http://localhost:8000`. Interactive Swagger API docs are available at `http://localhost:8000/docs`.*

### 2. Launch Frontend UI
In a separate terminal:
```bash
cd sport-prediction-platform
./run_frontend.sh
```
*Frontend runs on `http://localhost:3000` with automatic dev proxy to the backend API.*

---

## 🧪 Running the Test Suite

The test suite covers database schemas, the Dixon-Coles engine, the value bet detector, historical ingestion, backtest simulation, and all REST API endpoints.

```bash
cd sport-prediction-platform/backend
python3 -m pytest tests/ -v
```

All 28 tests run in strict TDD compliance:
```
======================== 28 passed in 8.62s ========================
```

---

## 📁 Repository Structure

```
sport-prediction-platform/
├── backend/
│   ├── app/
│   │   ├── engine/
│   │   │   ├── dixon_coles.py     # Dixon-Coles bivariate Poisson modeling
│   │   │   ├── value_detector.py  # +EV edge scanner and fractional Kelly staking
│   │   │   └── backtester.py      # Historical simulation and equity curve engine
│   │   ├── models/
│   │   │   └── schema.py          # SQLAlchemy SQLite models (League, Team, Match, Prediction)
│   │   ├── pipeline/
│   │   │   ├── historical.py      # Football-Data.co.uk CSV data loader
│   │   │   ├── live_feed.py       # Live fixture manager with sample fallback
│   │   │   └── sample_data.py     # Seed league & match fixtures with realistic odds
│   │   ├── routes/
│   │   │   ├── fixtures.py        # /api/leagues and /api/fixtures
│   │   │   ├── predictions.py     # /api/predictions
│   │   │   ├── value_bets.py      # /api/value-bets
│   │   │   └── backtest.py        # /api/backtest
│   │   ├── config.py              # Environment configuration
│   │   ├── database.py            # SQLite session and engine setup
│   │   └── main.py                # FastAPI app with CORS and lifespan handler
│   ├── requirements.txt
│   └── tests/                     # 28 comprehensive unit & integration tests
├── frontend/
│   ├── src/
│   │   ├── components/
│   │   │   ├── Navbar.jsx         # Header and tab switcher
│   │   │   ├── LeagueFilter.jsx   # League filter pill bar
│   │   │   ├── MatchCard.jsx      # Match fixture card with probability gauges
│   │   │   ├── MatchModal.jsx     # 7x7 score heatmap deep-dive modal
│   │   │   ├── ValueBetScanner.jsx# +EV scanner table and controls
│   │   │   └── BacktestLab.jsx    # Strategy backtester and equity curve
│   │   ├── services/
│   │   │   └── api.js             # Frontend API client
│   │   ├── App.jsx                # Main application orchestrator
│   │   ├── index.css              # Tailwind CSS directives
│   │   └── main.jsx               # React 18 entrypoint
│   ├── index.html
│   ├── package.json
│   ├── tailwind.config.js
│   └── vite.config.js
├── run_backend.sh
├── run_frontend.sh
└── README.md
```

---

## ⚖️ Mathematical Formulation

### Dixon-Coles Probability Specification
$$P(X=x, Y=y) = \tau_{\lambda, \mu}(x, y) \cdot \frac{\lambda^x e^{-\lambda}}{x!} \cdot \frac{\mu^y e^{-\mu}}{y!}$$

Where:
$$\lambda = \alpha_i \cdot \beta_j \cdot \gamma \quad (\text{Home } xG)$$
$$\mu = \alpha_j \cdot \beta_i \quad (\text{Away } xG)$$

Low-score correlation adjustment factor $\tau$:
$$\tau_{\lambda, \mu}(x, y) = \begin{cases}
1 - \lambda \mu \rho & \text{if } x=0, y=0 \\
1 + \lambda \rho & \text{if } x=0, y=1 \\
1 + \mu \rho & \text{if } x=1, y=0 \\
1 - \rho & \text{if } x=1, y=1 \\
1 & \text{otherwise}
\end{cases}$$

### Kelly Criterion Staking
$$f^* = c \cdot \frac{b \cdot p - q}{b}$$
- $p$: Model estimated win probability
- $q = 1 - p$: Model estimated loss probability
- $b = \text{Odds} - 1$: Net decimal payout
- $c = 0.25$: Fractional safety multiplier (Quarter-Kelly)
