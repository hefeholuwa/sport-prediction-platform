import React from 'react';

const LEAGUES = [
  { id: 'ALL', name: 'All Competitions' },
  { id: 'E0', name: 'Premier League' },
  { id: 'SP1', name: 'La Liga' },
  { id: 'I1', name: 'Serie A' },
  { id: 'D1', name: 'Bundesliga' },
  { id: 'F1', name: 'Ligue 1' }
];

export default function LeagueFilter({ selectedLeague, onSelectLeague }) {
  return (
    <div className="flex space-x-2 overflow-x-auto pb-2 scrollbar-none">
      {LEAGUES.map(league => (
        <button
          key={league.id}
          onClick={() => onSelectLeague(league.id)}
          className={`px-3 py-1.5 rounded-full text-xs font-medium whitespace-nowrap transition-colors ${
            selectedLeague === league.id
              ? 'bg-emerald-500/20 text-emerald-300 border border-emerald-500/50'
              : 'bg-slate-800/80 text-slate-400 hover:bg-slate-800 border border-slate-700/50'
          }`}
        >
          {league.name}
        </button>
      ))}
    </div>
  );
}
