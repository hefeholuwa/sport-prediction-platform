# SportyBet Live Odds Connector & Action Center Implementation Plan

**Goal:** Integrate SportyBet's live odds feed directly into ApexPredict, scan for $+EV$ betting edges in real time, and generate a daily actionable betslip (Action Sheet) for consistent daily profits.

---

### Proposed Changes

#### Backend Pipeline
- Create `sport-prediction-platform/backend/app/pipeline/sportybet.py`
  - `SportyBetConnector`:
    - Handles requests to `https://www.sportybet.com/api/ng/factsCenter/pcEvents` with Sportradar tournament IDs (`sr:tournament:17`, `sr:tournament:8`, etc.).
    - Robust headers, timeout handling, and graceful fallback to cached/sample data if offline.
    - Parses 1X2, Over/Under 2.5, and GG/NG (BTTS) odds into clean standardized dictionaries.
    - Normalizes SportyBet team naming ("Man City" -> "Manchester City", "Man Utd" -> "Manchester United", "Athletic Bilbao" -> "Athletic Club", etc.).

#### REST API
- Create `sport-prediction-platform/backend/app/routes/sportybet.py`
  - `GET /api/sportybet/fixtures`: Return live SportyBet fixtures with odds.
  - `GET /api/sportybet/value-bets`: Cross-reference SportyBet odds with Dixon-Coles engine to detect $+EV$ opportunities.
  - `POST /api/sportybet/action-sheet`: Daily action sheet generator for SportyBet (singles + 2-leg conservative accumulator with Kelly staking in ₦ or $).
- Register router in `sport-prediction-platform/backend/app/main.py`.

#### Tests
- Create `sport-prediction-platform/backend/tests/test_sportybet.py`
  - Test parsing of SportyBet JSON payloads.
  - Test team name normalization.
  - Test SportyBet API endpoints (`/api/sportybet/fixtures`, `/api/sportybet/value-bets`, `/api/sportybet/action-sheet`).

#### Frontend UI
- Update `sport-prediction-platform/frontend/src/services/api.js`
  - Add `fetchSportyBetFixtures(leagueId)`, `fetchSportyBetValueBets(minEv, market, leagueId)`, and `generateSportyBetActionSheet(params)`.
- Create `sport-prediction-platform/frontend/src/components/SportyBetTab.jsx`
  - Bankroll & Currency Settings (Naira ₦ or $).
  - "Today's SportyBet Action Sheet" displaying:
    - Top Recommended Singles with exact SportyBet market names and Naira stake.
    - Conservative 2-Leg Value Accumulator.
    - 1-Click "Copy Bet Details" to clipboard for easy pasting into SportyBet app.
  - Live SportyBet Edge Scanner table.
- Update `Navbar.jsx` and `App.jsx` to include the SportyBet tab.

---

### Verification Plan
1. `pytest tests/test_sportybet.py -v`: Verify all SportyBet tests pass.
2. `pytest tests/ -v`: Verify the entire backend test suite passes with 0 regressions.
3. `npm run build`: Verify the frontend builds with 0 errors.
4. Test live endpoint queries and frontend render in browser.
