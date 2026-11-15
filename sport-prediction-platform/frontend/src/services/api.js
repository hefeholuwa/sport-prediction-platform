const API_BASE = import.meta.env.VITE_API_BASE_URL || "/api";

export async function fetchLeagues() {
  const res = await fetch(`${API_BASE}/leagues`);
  if (!res.ok) throw new Error("Failed to fetch leagues");
  return res.json();
}

export async function fetchPredictions(leagueId = "ALL") {
  const url = !leagueId || leagueId === "ALL" 
    ? `${API_BASE}/predictions` 
    : `${API_BASE}/predictions?league_id=${encodeURIComponent(leagueId)}`;
  const res = await fetch(url);
  if (!res.ok) throw new Error("Failed to fetch predictions");
  return res.json();
}

export async function fetchValueBets(minEv = 0.03, market = "ALL", leagueId = "ALL") {
  const params = new URLSearchParams();
  if (minEv !== undefined && minEv !== null) params.append("min_ev", minEv.toString());
  if (market && market !== "ALL") params.append("market", market);
  if (leagueId && leagueId !== "ALL") params.append("league_id", leagueId);

  const res = await fetch(`${API_BASE}/value-bets?${params.toString()}`);
  if (!res.ok) throw new Error("Failed to fetch value bets");
  return res.json();
}

export async function runBacktestSimulation(params) {
  const res = await fetch(`${API_BASE}/backtest`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(params)
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    throw new Error(err.detail || "Failed to execute backtest simulation");
  }
  return res.json();
}

export async function fetchSportyBetFixtures(leagueId = "ALL") {
  const url = !leagueId || leagueId === "ALL"
    ? `${API_BASE}/sportybet/fixtures`
    : `${API_BASE}/sportybet/fixtures?league_id=${encodeURIComponent(leagueId)}`;
  const res = await fetch(url);
  if (!res.ok) throw new Error("Failed to fetch SportyBet fixtures");
  return res.json();
}

export async function fetchSportyBetValueBets(minEv = 0.03, market = "ALL", leagueId = "ALL", timeframe = "all") {
  const params = new URLSearchParams();
  if (minEv !== undefined && minEv !== null) params.append("min_ev", minEv.toString());
  if (market && market !== "ALL") params.append("market", market);
  if (leagueId && leagueId !== "ALL") params.append("league_id", leagueId);
  if (timeframe && timeframe !== "all") params.append("timeframe", timeframe);

  const res = await fetch(`${API_BASE}/sportybet/value-bets?${params.toString()}`);
  if (!res.ok) throw new Error("Failed to fetch SportyBet value bets");
  return res.json();
}

export async function fetchSportyBetActionSheet(params = {}) {
  const res = await fetch(`${API_BASE}/sportybet/action-sheet`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(params)
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    throw new Error(err.detail || "Failed to generate SportyBet Action Sheet");
  }
  return res.json();
}
