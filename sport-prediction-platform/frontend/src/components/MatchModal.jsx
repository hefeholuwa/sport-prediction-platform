import React, { useEffect } from 'react';
import { X, Award, Clock } from 'lucide-react';

export default function MatchModal({ item, onClose }) {
  useEffect(() => {
    function handleKeyDown(e) {
      if (e.key === 'Escape') onClose();
    }
    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [onClose]);

  if (!item) return null;

  const home_team = item?.home_team || 'Home';
  const away_team = item?.away_team || 'Away';
  const prediction = item?.prediction || {};
  const matrix = prediction.matrix || [];

  return (
    <div 
      onClick={onClose}
      className="fixed inset-0 z-50 bg-black/80 backdrop-blur-sm flex items-center justify-center p-4"
    >
      <div 
        onClick={e => e.stopPropagation()}
        className="bg-[#161F30] border border-slate-700/80 rounded-2xl max-w-2xl w-full max-h-[90vh] overflow-y-auto p-6 shadow-2xl"
      >
        <div className="flex justify-between items-start mb-6">
          <div>
            <h2 className="text-xl font-bold text-white">{home_team} vs {away_team}</h2>
            <div className="flex flex-wrap items-center gap-2 mt-1">
              <span className="text-xs font-mono bg-slate-800 text-slate-300 px-2 py-0.5 rounded border border-slate-700 flex items-center gap-1">
                <Clock className="h-3 w-3 text-emerald-400" />
                {item?.match_date || 'Upcoming'}
              </span>
              <span className="text-xs text-slate-400 font-mono">Dixon-Coles Scoreline Matrix & Probability Distribution</span>
            </div>
          </div>
          <button 
            onClick={onClose} 
            className="p-1 rounded-lg text-slate-400 hover:text-white hover:bg-slate-800 transition-colors"
          >
            <X className="h-5 w-5" />
          </button>
        </div>

        {/* 7x7 Heatmap */}
        <div className="mb-6">
          <h3 className="text-sm font-semibold text-slate-300 mb-3 flex items-center gap-1.5">
            <Award className="h-4 w-4 text-emerald-400" /> Exact Score Matrix (Home Goals vs Away Goals)
          </h3>
          <div className="overflow-x-auto bg-[#0F172A] p-4 rounded-xl border border-slate-800">
            <table className="w-full text-center text-xs border-collapse">
              <thead>
                <tr>
                  <th className="p-1 text-slate-500 font-mono">H \ A</th>
                  {[0, 1, 2, 3, 4, 5, 6].map(g => (
                    <th key={g} className="p-1 text-slate-400 font-mono font-bold">{g}</th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {matrix.map((row, hGoals) => (
                  <tr key={hGoals}>
                    <td className="p-1 font-mono font-bold text-slate-400">{hGoals}</td>
                    {row.map((prob, aGoals) => {
                      const pct = (prob * 100).toFixed(1);
                      const isHot = prob > 0.08;
                      const isHigh = prob > 0.12;
                      return (
                        <td
                          key={aGoals}
                          className={`p-1.5 font-mono text-[11px] rounded transition-colors ${
                            isHigh
                              ? 'bg-emerald-500/40 text-emerald-200 font-bold border border-emerald-500/60'
                              : isHot
                              ? 'bg-emerald-500/20 text-emerald-300'
                              : 'text-slate-500 hover:bg-slate-800'
                          }`}
                        >
                          {pct}%
                        </td>
                      );
                    })}
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>

        {/* Top Predictions Summary */}
        <div className="grid grid-cols-2 sm:grid-cols-3 gap-3 text-xs mb-4">
          <div className="bg-slate-800/50 p-3 rounded-lg border border-slate-700/50">
            <div className="text-slate-400 mb-1">Most Likely Score</div>
            <div className="text-lg font-bold font-mono text-emerald-400">{prediction.predicted_score || 'N/A'}</div>
          </div>
          <div className="bg-slate-800/50 p-3 rounded-lg border border-slate-700/50">
            <div className="text-slate-400 mb-1">Expected Goals (xG)</div>
            <div className="text-lg font-bold font-mono text-white">
              {prediction.home_xg ?? '-'} - {prediction.away_xg ?? '-'}
            </div>
          </div>
          <div className="bg-slate-800/50 p-3 rounded-lg border border-slate-700/50 col-span-2 sm:col-span-1">
            <div className="text-slate-400 mb-1">Over 2.5 Probability</div>
            <div className="text-lg font-bold font-mono text-amber-400">
              {prediction.over_2_5 !== undefined ? `${Math.round(prediction.over_2_5 * 100)}%` : 'N/A'}
            </div>
          </div>
        </div>

        <button
          onClick={onClose}
          className="w-full py-2 bg-slate-800 hover:bg-slate-700 text-white font-medium rounded-lg text-sm transition-colors"
        >
          Close Deep Dive
        </button>
      </div>
    </div>
  );
}
