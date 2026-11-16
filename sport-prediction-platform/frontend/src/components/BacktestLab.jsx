import React, { useState } from 'react';
import { BarChart2, Play, AlertTriangle } from 'lucide-react';
import { runBacktestSimulation } from '../services/api';

export default function BacktestLab() {
  const [minEv, setMinEv] = useState(0.04);
  const [staking, setStaking] = useState('flat');
  const [bankroll, setBankroll] = useState(1000);
  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  async function handleRun() {
    setLoading(true);
    setError(null);
    try {
      const data = await runBacktestSimulation({
        league_id: "E0",
        min_ev: minEv,
        staking: staking,
        initial_bankroll: bankroll
      });
      setResult(data);
    } catch (err) {
      console.error(err);
      setError(err.message || "Failed to run backtest simulation");
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="space-y-6">
      {/* Simulation Controls */}
      <div className="bg-[#161F30] border border-slate-800 p-5 rounded-xl">
        <h3 className="font-bold text-white text-base mb-4 flex items-center gap-2">
          <BarChart2 className="h-5 w-5 text-emerald-400" />
          Historical Strategy Backtester
        </h3>
        <div className="grid grid-cols-1 sm:grid-cols-4 gap-4 items-end">
          <div>
            <label className="block text-xs font-medium text-slate-400 mb-1.5">Initial Bankroll ($)</label>
            <input
              type="number"
              min="100"
              value={bankroll}
              onChange={e => setBankroll(Number(e.target.value))}
              className="w-full bg-[#0F172A] border border-slate-700 rounded-lg px-3 py-2 text-sm text-white font-mono focus:outline-none focus:border-emerald-500"
            />
          </div>
          <div>
            <label className="block text-xs font-medium text-slate-400 mb-1.5">Min EV Cutoff</label>
            <select
              value={minEv}
              onChange={e => setMinEv(Number(e.target.value))}
              className="w-full bg-[#0F172A] border border-slate-700 rounded-lg px-3 py-2 text-sm text-white font-mono focus:outline-none focus:border-emerald-500"
            >
              <option value={0.02}>+2% Edge</option>
              <option value={0.04}>+4% Edge</option>
              <option value={0.06}>+6% Edge</option>
              <option value={0.08}>+8% Edge</option>
            </select>
          </div>
          <div>
            <label className="block text-xs font-medium text-slate-400 mb-1.5">Staking Strategy</label>
            <select
              value={staking}
              onChange={e => setStaking(e.target.value)}
              className="w-full bg-[#0F172A] border border-slate-700 rounded-lg px-3 py-2 text-sm text-white focus:outline-none focus:border-emerald-500"
            >
              <option value="flat">Flat Staking ($25 / bet)</option>
              <option value="kelly">Fractional Kelly Criterion</option>
            </select>
          </div>
          <button
            onClick={handleRun}
            disabled={loading}
            className="w-full py-2.5 bg-emerald-500 hover:bg-emerald-400 text-slate-950 font-bold rounded-lg text-sm flex items-center justify-center gap-2 transition-colors disabled:opacity-50"
          >
            <Play className="h-4 w-4 fill-current" />
            {loading ? "Simulating..." : "Run Backtest"}
          </button>
        </div>
      </div>

      {error && (
        <div className="bg-red-500/10 border border-red-500/30 text-red-400 p-4 rounded-xl text-sm flex items-center gap-2">
          <AlertTriangle className="h-5 w-5 flex-shrink-0" />
          <span>{error}</span>
        </div>
      )}

      {/* Results View */}
      {result && (
        <div className="space-y-6">
          {/* KPI Cards */}
          <div className="grid grid-cols-2 sm:grid-cols-4 gap-4">
            <div className="bg-[#161F30] border border-slate-800 p-4 rounded-xl">
              <span className="text-xs text-slate-400">Total Profit / Loss</span>
              <div className={`text-xl font-bold font-mono mt-1 ${result.net_profit >= 0 ? 'text-emerald-400' : 'text-red-400'}`}>
                {result.net_profit >= 0 ? `+$${result.net_profit}` : `-$${Math.abs(result.net_profit)}`}
              </div>
            </div>
            <div className="bg-[#161F30] border border-slate-800 p-4 rounded-xl">
              <span className="text-xs text-slate-400">Return on Investment</span>
              <div className={`text-xl font-bold font-mono mt-1 ${result.roi_pct >= 0 ? 'text-emerald-400' : 'text-red-400'}`}>
                {result.roi_pct > 0 ? `+${result.roi_pct}%` : `${result.roi_pct}%`}
              </div>
            </div>
            <div className="bg-[#161F30] border border-slate-800 p-4 rounded-xl">
              <span className="text-xs text-slate-400">Win Rate (Strike Rate)</span>
              <div className="text-xl font-bold font-mono text-white mt-1">
                {result.strike_rate_pct}% ({result.winning_bets}/{result.total_bets})
              </div>
            </div>
            <div className="bg-[#161F30] border border-slate-800 p-4 rounded-xl">
              <span className="text-xs text-slate-400">Max Drawdown</span>
              <div className="text-xl font-bold font-mono text-amber-400 mt-1">
                {result.max_drawdown_pct}%
              </div>
            </div>
          </div>

          {/* Visual Equity Sequence */}
          <div className="bg-[#161F30] border border-slate-800 p-5 rounded-xl">
            <h4 className="text-sm font-semibold text-slate-300 mb-3">Equity Evolution Curve</h4>
            {(() => {
              const curve = result.equity_curve || [];
              const balances = curve.map(p => p.bankroll);
              const minVal = balances.length > 0 ? Math.min(...balances) : 0;
              const maxVal = balances.length > 0 ? Math.max(...balances) : 1000;
              const range = Math.max(1, maxVal - minVal);

              return (
                <div className="h-44 bg-[#0F172A] rounded-lg p-3 flex items-end space-x-1 overflow-x-auto">
                  {curve.map((pt, i) => {
                    const heightPct = Math.min(100, Math.max(10, ((pt.bankroll - minVal) / range) * 100));
                    return (
                      <div
                        key={i}
                        style={{ height: `${heightPct}%` }}
                        className="w-2.5 bg-emerald-500/80 hover:bg-emerald-400 rounded-t transition-all flex-shrink-0"
                        title={`Bet ${pt.step}: $${pt.bankroll}`}
                      />
                    );
                  })}
                </div>
              );
            })()}
            <div className="flex justify-between text-xs font-mono text-slate-500 mt-2">
              <span>Start: ${result.initial_bankroll}</span>
              <span>Final: ${result.final_bankroll}</span>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
