import React, { useState, useEffect } from 'react';
import { TrendingUp, AlertTriangle, RefreshCw, Calendar } from 'lucide-react';
import { fetchValueBets } from '../services/api';

export default function ValueBetScanner() {
  const [minEv, setMinEv] = useState(0.03);
  const [marketFilter, setMarketFilter] = useState('ALL');
  const [leagueFilter, setLeagueFilter] = useState('ALL');
  const [bets, setBets] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    loadBets();
  }, [minEv, marketFilter, leagueFilter]);

  async function loadBets() {
    setLoading(true);
    setError(null);
    try {
      const data = await fetchValueBets(minEv, marketFilter, leagueFilter);
      setBets(data);
    } catch (err) {
      console.error(err);
      setError(err.message || "Failed to scan value bets");
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="space-y-4">
      {/* Filters Bar */}
      <div className="bg-[#161F30] border border-slate-800 p-4 rounded-xl flex flex-wrap gap-4 items-center justify-between">
        <div className="flex items-center space-x-3">
          <TrendingUp className="h-5 w-5 text-emerald-400" />
          <span className="font-semibold text-white text-sm">Value Threshold:</span>
          <div className="flex space-x-1.5">
            {[0.02, 0.03, 0.05, 0.08].map(thresh => (
              <button
                key={thresh}
                onClick={() => setMinEv(thresh)}
                className={`px-3 py-1 rounded text-xs font-mono font-medium transition-colors ${
                  minEv === thresh
                    ? 'bg-emerald-500 text-slate-950 font-bold'
                    : 'bg-slate-800 text-slate-400 hover:bg-slate-700'
                }`}
              >
                +{Math.round(thresh * 100)}% EV
              </button>
            ))}
          </div>
        </div>

        <div className="flex items-center space-x-2 text-xs">
          <span className="text-slate-400">Market:</span>
          {['ALL', '1X2', 'Totals', 'BTTS'].map(m => (
            <button
              key={m}
              onClick={() => setMarketFilter(m)}
              className={`px-2.5 py-1 rounded transition-colors ${
                marketFilter === m
                  ? 'bg-slate-700 text-white font-medium border border-slate-600'
                  : 'text-slate-400 hover:text-white'
              }`}
            >
              {m}
            </button>
          ))}
        </div>
      </div>

      {/* Error Alert */}
      {error && (
        <div className="bg-red-500/10 border border-red-500/30 text-red-400 p-4 rounded-xl text-sm flex items-center justify-between">
          <div className="flex items-center gap-2">
            <AlertTriangle className="h-5 w-5 flex-shrink-0" />
            <span>{error}</span>
          </div>
          <button
            onClick={loadBets}
            className="flex items-center gap-1.5 px-3 py-1 bg-red-500/20 hover:bg-red-500/30 text-red-300 rounded text-xs font-medium transition-colors"
          >
            <RefreshCw className="h-3.5 w-3.5" /> Retry
          </button>
        </div>
      )}

      {/* Bets Table */}
      <div className="bg-[#161F30] border border-slate-800 rounded-xl overflow-hidden shadow-sm">
        {loading ? (
          <div className="p-8 text-center text-slate-400 text-sm">Scanning live fixtures for mathematical edges...</div>
        ) : error ? null : bets.length === 0 ? (
          <div className="p-8 text-center text-slate-400 text-sm">No value bets found above +{Math.round(minEv * 100)}% EV for the selected criteria.</div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs border-collapse">
              <thead>
                <tr className="bg-slate-800/70 border-b border-slate-700/60 text-slate-400 font-mono">
                  <th className="py-3 px-4">Fixture</th>
                  <th className="py-3 px-4">Market Pick</th>
                  <th className="py-3 px-4 text-center">Bookie Odds</th>
                  <th className="py-3 px-4 text-center">Model Fair</th>
                  <th className="py-3 px-4 text-center">Model Win %</th>
                  <th className="py-3 px-4 text-center">Expected Value</th>
                  <th className="py-3 px-4 text-right">Kelly Stake</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-800/80">
                {bets.map((bet, idx) => (
                  <tr key={idx} className="hover:bg-slate-800/40 transition-colors">
                    <td className="py-3 px-4">
                      <div className="font-medium text-white">{bet.fixture}</div>
                      <div className="text-[11px] text-slate-400 font-mono flex items-center gap-1.5 mt-0.5">
                        <Calendar className="h-3 w-3 text-slate-500 inline flex-shrink-0" />
                        <span>{bet.match_date || 'Upcoming'}</span>
                      </div>
                    </td>
                    <td className="py-3 px-4">
                      <span className="bg-emerald-500/10 text-emerald-400 font-semibold px-2 py-0.5 rounded border border-emerald-500/30">
                        {bet.selection}
                      </span>
                    </td>
                    <td className="py-3 px-4 text-center font-mono font-bold text-white">
                      {typeof bet.bookmaker_odds === 'number' ? bet.bookmaker_odds.toFixed(2) : bet.bookmaker_odds}
                    </td>
                    <td className="py-3 px-4 text-center font-mono text-slate-400">
                      {typeof bet.model_fair_odds === 'number' ? bet.model_fair_odds.toFixed(2) : bet.model_fair_odds}
                    </td>
                    <td className="py-3 px-4 text-center font-mono text-emerald-300">
                      {(bet.model_prob * 100).toFixed(1)}%
                    </td>
                    <td className="py-3 px-4 text-center font-mono font-bold text-emerald-400">
                      +{bet.ev_pct}%
                    </td>
                    <td className="py-3 px-4 text-right font-mono font-medium text-amber-300">
                      {(bet.recommended_kelly_stake * 100).toFixed(1)}% bankroll
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  );
}
