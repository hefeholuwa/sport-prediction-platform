# System Design Specification: SportyBet Live Odds Connector & Quantitative Betting Action Center

**Date:** 2026-11-15  
**Target Platform:** ApexPredict Full-Stack Football Prediction Platform  
**Integration Partner:** SportyBet (Nigeria / International via `api/ng/factsCenter`)  
**Status:** Approved  

---

## 1. Problem Statement & Motivation
The user wants to use **SportyBet** as the primary bookmaker to systematically generate daily profits from football betting. While the Dixon-Coles model generates statistical fair probabilities, successful sports betting requires exploiting real-time bookmaker mispricings ($+EV$). 

To make money consistently every day without falling victim to bookmaker vigorish (5–8%), the platform must:
1. Connect directly to SportyBet's production odds feed.
2. Cross-reference SportyBet's live market prices (1X2, Over/Under, GG/BTTS) against Dixon-Coles true probabilities.
3. Isolate the highest $+EV$ discrepancies where SportyBet has underpriced risk.
4. Output a clean **"Today's SportyBet Action Sheet"** with exact match IDs, SportyBet market names, and Kelly stakes in local currency (Naira ₦ or $) so the user can place bets quickly with zero guesswork.

---

## 2. Technical Architecture & Data Ingestion

```
┌────────────────────────────────────────────────────────┐
│               SportyBet FactsCenter API                │
│    POST https://www.sportybet.com/api/ng/factsCenter   │
│         /pcEvents  (Sportradar URNs, Market IDs)       │
└──────────────────────────┬─────────────────────────────┘
                           │ Real-time odds & fixtures
                           ▼
┌────────────────────────────────────────────────────────┐
│            SportyBet Connector Service                 │
│        (backend/app/pipeline/sportybet.py)             │
│   - Fetches Premier League, La Liga, Serie A, etc.     │
│   - Normalizes team names & market formats             │
│   - Extracts 1X2, Over/Under 2.5, GG/NG (BTTS) odds    │
└──────────────────────────┬─────────────────────────────┘
                           │
                           ▼
┌────────────────────────────────────────────────────────┐
│       Dixon-Coles Statistical Engine & Value Scanner    │
│             (backend/app/engine/dixon_coles.py)        │
│             (backend/app/engine/value_detector.py)     │
│   - Computes model true probabilities                  │
│   - Calculates exact EV: (P_model * Odds_sportybet) - 1│
│   - Sizes wagers via Fractional Kelly Criterion        │
└──────────────────────────┬─────────────────────────────┘
                           │
                           ▼
┌────────────────────────────────────────────────────────┐
│            SportyBet REST API Endpoints                │
│        (backend/app/routes/sportybet.py)               │
│   - GET  /api/sportybet/fixtures                       │
│   - GET  /api/sportybet/value-bets                     │
│   - POST /api/sportybet/action-sheet                   │
└──────────────────────────┬─────────────────────────────┘
                           │
                           ▼
┌────────────────────────────────────────────────────────┐
│            SportyBet Action Center UI                  │
│     (frontend/src/components/SportyBetTab.jsx)         │
│   - Live SportyBet Edge Table & Kelly Stake Sizing     │
│   - Curated "Today's Action Sheet" (Singles + Value 2X)│
│   - 1-Click "Copy SportyBet Bet Slip" button           │
└────────────────────────────────────────────────────────┘
```

---

## 3. Supported SportyBet Leagues & Markets

### A. Supported Tournaments (Sportradar IDs)
- **Premier League (England):** `sr:tournament:17` (Internal code: `E0`)
- **La Liga (Spain):** `sr:tournament:8` (Internal code: `SP1`)
- **Serie A (Italy):** `sr:tournament:23` (Internal code: `I1`)
- **Bundesliga (Germany):** `sr:tournament:35` (Internal code: `D1`)
- **Ligue 1 (France):** `sr:tournament:34` (Internal code: `F1`)

### B. Supported SportyBet Market IDs
- **Market 1 (1X2):** Home (`Home`), Draw (`Draw`), Away (`Away`)
- **Market 18 (Over/Under Goals):** Over 2.5, Under 2.5
- **Market 29 (GG / NG - Both Teams to Score):** Yes (`Yes`), No (`No`)

---

## 4. API Specification

### `GET /api/sportybet/fixtures`
**Parameters:**
- `league_id: Optional[str]` (e.g. `E0`, `SP1`, `ALL`)
**Returns:**
List of upcoming SportyBet fixtures with SportyBet event IDs, kickoff timestamps, and decimal odds for 1X2, Over/Under 2.5, and GG/NG.

### `GET /api/sportybet/value-bets`
**Parameters:**
- `min_ev: float = 0.03` (default 3% edge)
- `market: Optional[str]` (e.g. `1X2`, `Totals`, `BTTS`, `ALL`)
- `league_id: Optional[str]`
**Returns:**
Detected $+EV$ opportunities on SportyBet, sorted by edge descending, with model fair odds, SportyBet odds, EV%, and fractional Kelly stake %.

### `POST /api/sportybet/action-sheet`
**Payload:**
```json
{
  "bankroll": 50000.0,
  "currency": "NGN",
  "min_ev": 0.04,
  "max_bets": 5
}
```
**Returns:**
Curated action plan containing:
1. **Top Single Value Bets:** Recommended individual wagers with exact stake in Naira (or chosen currency).
2. **Conservative Value Double:** 2 highest-probability $+EV$ legs combined into a disciplined low-risk accumulator.
3. **Summary Metrics:** Total capital allocated, expected portfolio growth %, and composite probability.

---

## 5. Testing & Validation Strategy
1. **Pipeline Unit Tests:** Test SportyBet API payload serialization, response parsing, and error fallback.
2. **Team Name Resolution:** Test matching SportyBet team naming conventions ("Man City", "Aston Villa", "Newcastle", etc.) with Dixon-Coles model entities.
3. **API Integration Tests:** Test `/api/sportybet/fixtures`, `/api/sportybet/value-bets`, and `/api/sportybet/action-sheet`.
4. **UI Build & Verification:** Ensure seamless tab integration and clean compilation with Vite.
