import React, { useState, useEffect } from 'react';
import { Flame, Copy, Check, TrendingUp, AlertTriangle, RefreshCw, Zap, ShieldCheck, Calendar, Clock } from 'lucide-react';
import { fetchSportyBetActionSheet, fetchSportyBetValueBets } from '../services/api';

export default function SportyBetTab() {
  const [bankroll, setBankroll] = useState(50000);
  const [currency, setCurrency] = useState('NGN');
  const [minEv, setMinEv] = useState(0.03);
  const [maxBets, setMaxBets] = useState(5);
  const [strategy, setStrategy] = useState('compounder'); // 'compounder' | 'value'
  const [selectedComboTab, setSelectedComboTab] = useState('two_odds'); // 'two_odds' | 'five_odds' | 'ten_odds' | 'fifty_odds' | 'hundred_odds'
  const [actionSheet, setActionSheet] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [copiedId, setCopiedId] = useState(null);
  const [allCopied, setAllCopied] = useState(false);

  useEffect(() => {
    loadActionSheet();
  }, [bankroll, currency, minEv, maxBets, strategy]);

  async function loadActionSheet() {
    setLoading(true);
    setError(null);
    try {
      const data = await fetchSportyBetActionSheet({
        bankroll: Number(bankroll) || 50000,
        currency: currency,
        min_ev: Number(minEv),
        max_bets: Number(maxBets) || 5,
        strategy: strategy
      });
      setActionSheet(data);
    } catch (err) {
      console.error(err);
      setError(err.message || 'Failed to connect to SportyBet live feed');
    } finally {
      setLoading(false);
    }
  }

  function copySingle(bet, idx) {
    const timeStr = bet.match_date ? ` [${bet.match_date}]` : '';
    const text = `SportyBet Pick: ${bet.fixture}${timeStr} | Pick: ${bet.selection} | Odds: ${bet.sportybet_odds} | Edge: +${bet.ev_pct}% | Stake: ${currencySymbol()}${bet.stake_amount.toLocaleString()}`;
    navigator.clipboard.writeText(text);
    setCopiedId(idx);
    setTimeout(() => setCopiedId(null), 2000);
  }

  function copyCombo(combo, comboKey) {
    if (!combo) return;
    const legsText = combo.legs.map((l, i) => {
      const timeStr = l.match_date ? ` [${l.match_date}]` : '';
      return `${i + 1}. ${l.fixture}${timeStr} -> ${l.selection} (@${l.sportybet_odds}) [${l.prob_pct}% prob]`;
    }).join('\n');
    const text = `🎯 SPORTYBET ${combo.name.toUpperCase()}:\n${legsText}\n\nCombined Odds: @${combo.combined_odds}\nWin Probability: ${combo.combined_win_prob_pct}%\nRecommended Stake: ${currencySymbol()}${combo.stake_amount.toLocaleString()}\nPotential Return: ${currencySymbol()}${combo.potential_return.toLocaleString()}`;
    navigator.clipboard.writeText(text);
    setCopiedId(comboKey || 'combo');
    setTimeout(() => setCopiedId(null), 2000);
  }

  function copyEntireSlip() {
    if (!actionSheet) return;
    let text = `🔥 APEXPREDICT x SPORTYBET ACTION SHEET\nBankroll: ${currencySymbol()}${actionSheet.bankroll.toLocaleString()} | Staked: ${currencySymbol()}${actionSheet.total_allocated_stake.toLocaleString()} (${actionSheet.portfolio_allocation_pct}%)\n\n📌 TOP VALUE SINGLES:\n`;
    actionSheet.singles.forEach((s, i) => {
      const timeStr = s.match_date ? ` [${s.match_date}]` : '';
      text += `${i + 1}. ${s.fixture}${timeStr} -> ${s.selection} (@${s.sportybet_odds}) | Edge: +${s.ev_pct}% | Stake: ${currencySymbol()}${s.stake_amount.toLocaleString()}\n`;
    });
    if (actionSheet.combos) {
      Object.values(actionSheet.combos).forEach(c => {
        if (!c) return;
        text += `\n🎯 ${c.name.toUpperCase()} (@${c.combined_odds} | ${c.combined_win_prob_pct}% prob):\n`;
        c.legs.forEach(l => {
          const timeStr = l.match_date ? ` [${l.match_date}]` : '';
          text += `• ${l.fixture}${timeStr} -> ${l.selection} (@${l.sportybet_odds})\n`;
        });
        text += `Stake: ${currencySymbol()}${c.stake_amount.toLocaleString()} | Return: ${currencySymbol()}${c.potential_return.toLocaleString()}\n`;
      });
    }
    navigator.clipboard.writeText(text);
    setAllCopied(true);
    setTimeout(() => setAllCopied(false), 2500);
  }

  function currencySymbol() {
    if (currency === 'NGN') return '₦';
    if (currency === 'USD') return '$';
    if (currency === 'GBP') return '£';
    if (currency === 'EUR') return '€';
    return '';
  }

  return (
    <div className="space-y-6">
      {/* Header Banner */}
      <div className="bg-gradient-to-r from-red-950/40 via-[#161F30] to-[#161F30] border border-red-900/40 p-5 rounded-2xl flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <div className="flex items-center space-x-2">
            <span className="bg-red-600 text-white font-extrabold text-xs px-2.5 py-0.5 rounded tracking-wider uppercase">
              SportyBet Live Feed
            </span>
            <span className="flex items-center gap-1.5 text-xs text-emerald-400 bg-emerald-500/10 border border-emerald-500/30 px-2 py-0.5 rounded-full font-mono">
              <span className="h-1.5 w-1.5 rounded-full bg-emerald-400 animate-ping"></span> Connected
            </span>
          </div>
          <h2 className="text-xl font-bold text-white mt-1">Daily Quantitative Profit Hub</h2>
          <p className="text-xs text-slate-400 mt-0.5">
            Real-time SportyBet odds matched against Dixon-Coles probabilities. Only bets with mathematical edge are selected.
          </p>
        </div>

        <button
          onClick={copyEntireSlip}
          disabled={!actionSheet || actionSheet.singles?.length === 0}
          className="flex items-center gap-2 px-4 py-2 bg-red-600 hover:bg-red-500 text-white font-semibold rounded-lg text-xs shadow-lg shadow-red-900/30 transition-all disabled:opacity-50 flex-shrink-0"
        >
          {allCopied ? <Check className="h-4 w-4" /> : <Copy className="h-4 w-4" />}
          <span>{allCopied ? 'Action Sheet Copied!' : 'Copy Daily Action Slip'}</span>
        </button>
      </div>

      {/* Strategy Selector & Risk Management */}
      <div className="bg-[#161F30] border border-slate-800 p-3 rounded-2xl flex flex-col md:flex-row gap-3 items-center justify-between">
        <div className="flex bg-[#0F172A] p-1 rounded-xl w-full md:w-auto">
          <button
            onClick={() => setStrategy('compounder')}
            className={`flex-1 md:flex-none px-4 py-2 rounded-lg text-xs font-semibold flex items-center justify-center gap-2 transition-all ${
              strategy === 'compounder'
                ? 'bg-emerald-600 text-white shadow-md shadow-emerald-900/40'
                : 'text-slate-400 hover:text-slate-200'
            }`}
          >
            <Zap className="h-3.5 w-3.5" />
            <span>⚡ Daily Compounder (50%–85% Win Rate)</span>
          </button>
          <button
            onClick={() => setStrategy('value')}
            className={`flex-1 md:flex-none px-4 py-2 rounded-lg text-xs font-semibold flex items-center justify-center gap-2 transition-all ${
              strategy === 'value'
                ? 'bg-red-600 text-white shadow-md shadow-red-900/40'
                : 'text-slate-400 hover:text-slate-200'
            }`}
          >
            <Flame className="h-3.5 w-3.5" />
            <span>🎯 Pure Value Hunter (Odds ≤ 3.20)</span>
          </button>
        </div>

        <div className="flex items-center gap-2 px-3 py-1.5 rounded-lg bg-emerald-500/10 border border-emerald-500/30 text-xs text-emerald-300 w-full md:w-auto">
          <ShieldCheck className="h-4 w-4 text-emerald-400 flex-shrink-0" />
          <span>
            <b>Anti-Underdog Safeguard Active:</b> Longshots pruned. Odds capped at {strategy === 'compounder' ? '2.25' : '3.20'}.
          </span>
        </div>
      </div>

      {/* Settings Bar */}
      <div className="bg-[#161F30] border border-slate-800 p-4 rounded-xl grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4 items-center">
        <div>
          <label className="block text-xs font-medium text-slate-400 mb-1">Bankroll Setting</label>
          <div className="flex rounded-lg overflow-hidden border border-slate-700">
            <select
              value={currency}
              onChange={e => setCurrency(e.target.value)}
              className="bg-slate-800 text-white text-xs px-3 py-2 font-mono border-r border-slate-700 focus:outline-none"
            >
              <option value="NGN">NGN (₦)</option>
              <option value="USD">USD ($)</option>
              <option value="GBP">GBP (£)</option>
              <option value="EUR">EUR (€)</option>
            </select>
            <input
              type="number"
              value={bankroll}
              onChange={e => setBankroll(Number(e.target.value))}
              className="w-full bg-[#0F172A] px-3 py-2 text-sm text-white font-mono focus:outline-none"
              placeholder="e.g. 50000"
            />
          </div>
        </div>

        <div>
          <label className="block text-xs font-medium text-slate-400 mb-1">Picks Per Day</label>
          <div className="flex space-x-1">
            {[3, 5, 8, 10].map(cnt => (
              <button
                key={cnt}
                onClick={() => setMaxBets(cnt)}
                className={`flex-1 py-1.5 rounded text-xs font-mono font-medium transition-colors ${
                  maxBets === cnt
                    ? 'bg-emerald-600 text-white font-bold'
                    : 'bg-slate-800 text-slate-400 hover:bg-slate-700'
                }`}
              >
                {cnt}
              </button>
            ))}
          </div>
        </div>

        <div>
          <label className="block text-xs font-medium text-slate-400 mb-1">Minimum Edge (+EV)</label>
          <div className="flex space-x-1">
            {[0.02, 0.03, 0.05, 0.08].map(ev => (
              <button
                key={ev}
                onClick={() => setMinEv(ev)}
                className={`flex-1 py-1.5 rounded text-xs font-mono font-medium transition-colors ${
                  minEv === ev
                    ? 'bg-red-600 text-white font-bold'
                    : 'bg-slate-800 text-slate-400 hover:bg-slate-700'
                }`}
              >
                +{Math.round(ev * 100)}%
              </button>
            ))}
          </div>
        </div>

        <div className="flex sm:justify-end items-end h-full">
          <button
            onClick={loadActionSheet}
            disabled={loading}
            className="w-full px-4 py-2 bg-slate-800 hover:bg-slate-700 text-slate-200 rounded-lg text-xs font-medium flex items-center justify-center gap-1.5 transition-colors"
          >
            <RefreshCw className={`h-3.5 w-3.5 ${loading ? 'animate-spin' : ''}`} />
            <span>Refresh Odds</span>
          </button>
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
            onClick={loadActionSheet}
            className="flex items-center gap-1.5 px-3 py-1 bg-red-500/20 hover:bg-red-500/30 text-red-300 rounded text-xs font-medium transition-colors"
          >
            <RefreshCw className="h-3.5 w-3.5" /> Retry
          </button>
        </div>
      )}

      {loading ? (
        <div className="text-center py-20 text-slate-400 text-sm flex flex-col items-center justify-center space-y-2">
          <div className="h-6 w-6 border-2 border-red-500 border-t-transparent rounded-full animate-spin"></div>
          <span>Matching live SportyBet odds with statistical probabilities...</span>
        </div>
      ) : actionSheet && (
        <div className="space-y-6">
          {/* Portfolio Summary Card */}
          <div className="grid grid-cols-2 sm:grid-cols-4 gap-4">
            <div className="bg-[#161F30] border border-slate-800 p-4 rounded-xl">
              <span className="text-xs text-slate-400">Total Capital Staked</span>
              <div className="text-xl font-bold font-mono text-white mt-1">
                {currencySymbol()}{actionSheet.total_allocated_stake?.toLocaleString()}
              </div>
            </div>
            <div className="bg-[#161F30] border border-slate-800 p-4 rounded-xl">
              <span className="text-xs text-slate-400">Portfolio Allocation</span>
              <div className="text-xl font-bold font-mono text-emerald-400 mt-1">
                {actionSheet.portfolio_allocation_pct}%
              </div>
            </div>
            <div className="bg-[#161F30] border border-slate-800 p-4 rounded-xl">
              <span className="text-xs text-slate-400">Qualified Singles</span>
              <div className="text-xl font-bold font-mono text-white mt-1">
                {actionSheet.singles?.length || 0} picks
              </div>
            </div>
            <div className="bg-[#161F30] border border-slate-800 p-4 rounded-xl">
              <span className="text-xs text-slate-400">Risk Management</span>
              <div className="text-sm font-semibold text-emerald-400 mt-1 flex items-center gap-1">
                <ShieldCheck className="h-4 w-4" /> Quarter-Kelly Cap
              </div>
            </div>
          </div>

          {/* Multi-Tier Acca Combos Hub (2, 5, 10, 50, 100 Odds) */}
          {(actionSheet.combos || actionSheet.conservative_double) && (() => {
            const activeCombo = actionSheet.combos ? actionSheet.combos[selectedComboTab] : actionSheet.conservative_double;
            return (
              <div className="bg-gradient-to-br from-[#161F30] to-[#1E293B] border border-slate-800 rounded-2xl p-5 shadow-lg relative overflow-hidden">
                <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 mb-4">
                  <div className="flex items-center gap-2">
                    <span className="p-1.5 rounded-lg bg-red-600/20 text-red-400">
                      <Zap className="h-5 w-5" />
                    </span>
                    <div>
                      <h3 className="text-base font-bold text-white">SportyBet Accumulator & Combo Hub</h3>
                      <p className="text-xs text-slate-400">Targeted multiplier slips built from statistically vetted non-correlated legs</p>
                    </div>
                  </div>

                  {activeCombo && (
                    <button
                      onClick={() => copyCombo(activeCombo, selectedComboTab)}
                      className="flex items-center gap-1.5 px-3 py-1.5 bg-red-600 hover:bg-red-500 text-white rounded-lg text-xs font-semibold shadow-md shadow-red-900/30 transition-colors self-start sm:self-auto"
                    >
                      {copiedId === selectedComboTab ? <Check className="h-3.5 w-3.5" /> : <Copy className="h-3.5 w-3.5" />}
                      <span>{copiedId === selectedComboTab ? 'Slip Copied!' : `Copy ${activeCombo.name}`}</span>
                    </button>
                  )}
                </div>

                {/* Combo Tier Tabs */}
                {actionSheet.combos && (
                  <div className="grid grid-cols-2 sm:grid-cols-5 gap-1.5 p-1 bg-[#0F172A] rounded-xl mb-4 border border-slate-800">
                    {[
                      { id: 'two_odds', label: '2 Sure Odds', badge: 'Banker' },
                      { id: 'five_odds', label: '5 Sure Odds', badge: 'Multiplier' },
                      { id: 'ten_odds', label: '10 Odds', badge: 'Weekend Value' },
                      { id: 'fifty_odds', label: '50 Mega Odds', badge: 'Jackpot' },
                      { id: 'hundred_odds', label: '100 Mega Odds', badge: 'Super Ticket' },
                    ].map(tab => {
                      const comboData = actionSheet.combos[tab.id];
                      const isSelected = selectedComboTab === tab.id;
                      return (
                        <button
                          key={tab.id}
                          onClick={() => setSelectedComboTab(tab.id)}
                          disabled={!comboData}
                          className={`py-2 px-2.5 rounded-lg text-xs font-semibold flex flex-col items-center gap-0.5 transition-all ${
                            isSelected
                              ? 'bg-red-600 text-white shadow-md shadow-red-900/40'
                              : comboData
                              ? 'text-slate-300 hover:bg-slate-800/80 hover:text-white'
                              : 'text-slate-600 cursor-not-allowed opacity-50'
                          }`}
                        >
                          <span className="font-bold">{tab.label}</span>
                          <span className={`text-[10px] font-mono ${isSelected ? 'text-white/80' : 'text-slate-400'}`}>
                            {comboData ? `@${comboData.combined_odds} (${comboData.legs_count}L)` : 'N/A'}
                          </span>
                        </button>
                      );
                    })}
                  </div>
                )}

                {/* Active Combo Body */}
                {activeCombo ? (
                  <div className="space-y-4">
                    <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-2.5 max-h-80 overflow-y-auto pr-1">
                      {activeCombo.legs.map((leg, idx) => (
                        <div key={idx} className="bg-[#0F172A] p-2.5 rounded-xl border border-slate-800 flex justify-between items-center hover:border-slate-700 transition-colors">
                          <div className="min-w-0 pr-2">
                            <div className="font-semibold text-xs text-white truncate">{leg.fixture}</div>
                            <div className="flex items-center gap-2 mt-0.5">
                              <span className="text-[11px] text-emerald-400 font-medium truncate">{leg.selection}</span>
                              <span className="text-[10px] text-slate-400 font-mono flex items-center gap-0.5 flex-shrink-0">
                                <Clock className="h-2.5 w-2.5 text-slate-500 inline" /> {leg.match_date || 'Upcoming'}
                              </span>
                            </div>
                          </div>
                          <div className="text-right flex-shrink-0">
                            <div className="font-mono font-bold text-white text-xs">@{leg.sportybet_odds}</div>
                            <div className="text-[10px] text-slate-400 font-mono">{leg.prob_pct}% prob</div>
                          </div>
                        </div>
                      ))}
                    </div>

                    <div className="flex flex-wrap items-center justify-between pt-3 border-t border-slate-800 text-xs font-mono">
                      <div className="flex flex-wrap gap-x-4 gap-y-1">
                        <span>Combined Odds: <b className="text-emerald-400">@{activeCombo.combined_odds}</b></span>
                        <span>Win Probability: <b className="text-white">{activeCombo.combined_win_prob_pct}%</b></span>
                        <span>Total Legs: <b className="text-slate-300">{activeCombo.legs_count}</b></span>
                      </div>
                      <div className="flex flex-wrap gap-x-4 gap-y-1 mt-2 sm:mt-0">
                        <span>Recommended Stake: <b className="text-amber-400">{currencySymbol()}{activeCombo.stake_amount.toLocaleString()}</b></span>
                        <span>Potential Payout: <b className="text-emerald-400 font-bold">{currencySymbol()}{activeCombo.potential_return.toLocaleString()}</b></span>
                      </div>
                    </div>
                  </div>
                ) : (
                  <div className="text-center py-8 text-xs text-slate-400">
                    Combo slip not available for this tier with current edge filters.
                  </div>
                )}
              </div>
            );
          })()}

          {/* Top Singles Table */}
          <div className="bg-[#161F30] border border-slate-800 rounded-2xl overflow-hidden shadow-sm">
            <div className="p-4 border-b border-slate-800 flex items-center justify-between">
              <h3 className="font-bold text-white text-sm flex items-center gap-2">
                <Flame className="h-4 w-4 text-red-500" />
                Today's Recommended SportyBet Singles
              </h3>
              <span className="text-xs text-slate-400 font-mono">Ranked by Expected Value (+EV)</span>
            </div>

            {actionSheet.singles?.length === 0 ? (
              <div className="p-10 text-center text-slate-400 text-sm">
                No matches currently exceed the +{Math.round(minEv * 100)}% edge threshold on SportyBet. Try lowering the edge cutoff to +2%.
              </div>
            ) : (
              <div className="overflow-x-auto">
                <table className="w-full text-left text-xs border-collapse">
                  <thead>
                    <tr className="bg-slate-800/60 border-b border-slate-700/60 text-slate-400 font-mono">
                      <th className="py-3 px-4">Fixture</th>
                      <th className="py-3 px-4">SportyBet Market Pick</th>
                      <th className="py-3 px-4 text-center">SportyBet Odds</th>
                      <th className="py-3 px-4 text-center">Model Win Prob</th>
                      <th className="py-3 px-4 text-center">Mathematical Edge</th>
                      <th className="py-3 px-4 text-right">Kelly Stake</th>
                      <th className="py-3 px-4 text-right">Potential Win</th>
                      <th className="py-3 px-4 text-center">Action</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-slate-800/80">
                    {actionSheet.singles.map((bet, idx) => (
                      <tr key={idx} className="hover:bg-slate-800/40 transition-colors">
                        <td className="py-3.5 px-4">
                          <div className="font-semibold text-white">{bet.fixture}</div>
                          <div className="text-[11px] text-slate-400 font-mono flex items-center gap-1.5 mt-0.5">
                            <Calendar className="h-3 w-3 text-slate-500 inline flex-shrink-0" />
                            <span>{bet.match_date || 'Upcoming'}</span>
                          </div>
                        </td>
                        <td className="py-3.5 px-4">
                          <span className="bg-red-500/10 text-red-300 font-semibold px-2 py-0.5 rounded border border-red-500/30">
                            {bet.selection} ({bet.market})
                          </span>
                        </td>
                        <td className="py-3.5 px-4 text-center font-mono font-bold text-white">
                          {bet.sportybet_odds.toFixed(2)}
                        </td>
                        <td className="py-3.5 px-4 text-center font-mono">
                          {bet.model_prob_pct >= 55 ? (
                            <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded text-[11px] font-bold bg-emerald-500/20 text-emerald-300 border border-emerald-500/30">
                              🔥 {bet.model_prob_pct}%
                            </span>
                          ) : (
                            <span className="text-slate-300 font-medium">{bet.model_prob_pct}%</span>
                          )}
                        </td>
                        <td className="py-3.5 px-4 text-center font-mono font-bold text-emerald-400">
                          +{bet.ev_pct}%
                        </td>
                        <td className="py-3.5 px-4 text-right font-mono font-bold text-amber-300">
                          {currencySymbol()}{bet.stake_amount.toLocaleString()}
                          <span className="block text-[10px] text-slate-400 font-normal">({bet.recommended_stake_pct}%)</span>
                        </td>
                        <td className="py-3.5 px-4 text-right font-mono font-bold text-white">
                          {currencySymbol()}{bet.potential_return.toLocaleString()}
                        </td>
                        <td className="py-3.5 px-4 text-center">
                          <button
                            onClick={() => copySingle(bet, idx)}
                            className="p-1.5 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-300 hover:text-white transition-colors"
                            title="Copy bet to clipboard"
                          >
                            {copiedId === idx ? <Check className="h-4 w-4 text-emerald-400" /> : <Copy className="h-4 w-4" />}
                          </button>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
}
