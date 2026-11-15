import React from 'react';
import { Target, Zap, ChevronRight } from 'lucide-react';

export default function MatchCard({ item, onSelectMatch }) {
  const { home_team, away_team, match_date, odds, prediction } = item;
  const p = prediction;

  const homePct = Math.round(p.home_win * 100);
  const drawPct = Math.round(p.draw * 100);
  const awayPct = Math.round(p.away_win * 100);

  // Check for value bet on 1X2
  const homeEV = Math.round(((p.home_win * odds.home) - 1) * 100);
  const awayEV = Math.round(((p.away_win * odds.away) - 1) * 100);
  const hasValue = homeEV >= 5 || awayEV >= 5;

  return (
    <div className="bg-[#161F30] border border-slate-800/80 hover:border-slate-700 rounded-xl p-5 shadow-sm transition-all hover:shadow-md flex flex-col justify-between">
      <div>
        <div className="flex items-center justify-between text-xs text-slate-400 mb-3">
          <span className="font-mono bg-slate-800/80 px-2 py-0.5 rounded text-slate-300 border border-slate-700/60">
            {match_date}
          </span>
          {hasValue && (
            <span className="flex items-center gap-1 text-[11px] font-semibold text-emerald-400 bg-emerald-500/10 border border-emerald-500/30 px-2 py-0.5 rounded-full animate-pulse">
              <Zap className="h-3 w-3" /> +EV EDGE
            </span>
          )}
        </div>

        {/* Teams & xG */}
        <div className="space-y-2 mb-4">
          <div className="flex justify-between items-center">
            <span className="font-semibold text-white text-base">{home_team}</span>
            <span className="font-mono text-sm font-medium text-emerald-400 bg-slate-800/60 px-2 py-0.5 rounded border border-slate-700/40">
              xG {p.home_xg}
            </span>
          </div>
          <div className="flex justify-between items-center">
            <span className="font-semibold text-white text-base">{away_team}</span>
            <span className="font-mono text-sm font-medium text-slate-400 bg-slate-800/60 px-2 py-0.5 rounded border border-slate-700/40">
              xG {p.away_xg}
            </span>
          </div>
        </div>

        {/* 1X2 Tri-Color Probability Gauge */}
        <div className="mb-4">
          <div className="flex justify-between text-xs font-mono text-slate-300 mb-1">
            <span>1: {homePct}% ({odds.home})</span>
            <span>X: {drawPct}% ({odds.draw})</span>
            <span>2: {awayPct}% ({odds.away})</span>
          </div>
          <div className="h-2.5 w-full bg-slate-800 rounded-full overflow-hidden flex">
            <div style={{ width: `${homePct}%` }} className="bg-emerald-500 h-full" title={`Home: ${homePct}%`} />
            <div style={{ width: `${drawPct}%` }} className="bg-amber-500 h-full" title={`Draw: ${drawPct}%`} />
            <div style={{ width: `${awayPct}%` }} className="bg-blue-500 h-full" title={`Away: ${awayPct}%`} />
          </div>
        </div>

        {/* Secondary Markets */}
        <div className="grid grid-cols-2 gap-2 text-xs mb-4">
          <div className="bg-slate-800/40 border border-slate-800 p-2 rounded-lg flex justify-between items-center">
            <span className="text-slate-400">Over 2.5:</span>
            <span className="font-mono font-semibold text-white">{Math.round(p.over_2_5 * 100)}%</span>
          </div>
          <div className="bg-slate-800/40 border border-slate-800 p-2 rounded-lg flex justify-between items-center">
            <span className="text-slate-400">BTTS Yes:</span>
            <span className="font-mono font-semibold text-white">{Math.round(p.btts_yes * 100)}%</span>
          </div>
        </div>
      </div>

      <div className="pt-3 border-t border-slate-800 flex items-center justify-between">
        <div className="text-xs text-slate-400 flex items-center gap-1.5">
          <Target className="h-3.5 w-3.5 text-emerald-400" />
          <span>Pred: <b className="text-white">{p.predicted_score}</b></span>
        </div>
        <button
          onClick={() => onSelectMatch(item)}
          className="text-xs text-emerald-400 hover:text-emerald-300 font-medium flex items-center gap-0.5 hover:underline"
        >
          Deep Dive <ChevronRight className="h-3.5 w-3.5" />
        </button>
      </div>
    </div>
  );
}
