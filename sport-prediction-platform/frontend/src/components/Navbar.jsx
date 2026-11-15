import React from 'react';
import { Activity, TrendingUp, BarChart2, ShieldCheck, Flame } from 'lucide-react';

export default function Navbar({ activeTab, setActiveTab }) {
  const navItems = [
    { id: 'predictions', label: 'Predictions', icon: Activity },
    { id: 'sportybet', label: 'SportyBet +EV', icon: Flame, isSpecial: true },
    { id: 'value-scanner', label: 'Value Bet Scanner', icon: TrendingUp },
    { id: 'backtest', label: 'Backtest Lab', icon: BarChart2 }
  ];

  return (
    <header className="border-b border-slate-800 bg-[#0F172A] sticky top-0 z-40">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 h-16 flex items-center justify-between">
        <div className="flex items-center space-x-3">
          <div className="h-9 w-9 rounded-lg bg-emerald-500/20 border border-emerald-500/40 flex items-center justify-center text-emerald-400">
            <ShieldCheck className="h-5 w-5" />
          </div>
          <div>
            <h1 className="font-bold text-lg text-white tracking-tight flex items-center gap-2">
              APEX<span className="text-emerald-400">PREDICT</span>
              <span className="text-[10px] uppercase font-mono px-1.5 py-0.5 rounded bg-emerald-500/10 text-emerald-400 border border-emerald-500/30">
                Dixon-Coles AI
              </span>
            </h1>
          </div>
        </div>

        <nav className="flex space-x-1 sm:space-x-2">
          {navItems.map(item => {
            const Icon = item.icon;
            const active = activeTab === item.id;
            return (
              <button
                key={item.id}
                onClick={() => setActiveTab(item.id)}
                className={`flex items-center space-x-2 px-3 py-1.5 rounded-lg text-sm font-medium transition-all ${
                  active
                    ? item.isSpecial
                      ? 'bg-red-600 text-white font-semibold shadow-lg shadow-red-600/30'
                      : 'bg-emerald-500 text-slate-950 font-semibold shadow-lg shadow-emerald-500/20'
                    : item.isSpecial
                    ? 'text-red-400 hover:text-white hover:bg-red-950/40 border border-red-900/30'
                    : 'text-slate-400 hover:text-white hover:bg-slate-800'
                }`}
              >
                <Icon className={`h-4 w-4 ${item.isSpecial && !active ? 'text-red-500 animate-pulse' : ''}`} />
                <span className="hidden sm:inline">{item.label}</span>
              </button>
            );
          })}
        </nav>
      </div>
    </header>
  );
}
