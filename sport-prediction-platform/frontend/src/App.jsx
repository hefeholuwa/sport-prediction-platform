import React, { useState, useEffect } from 'react';
import Navbar from './components/Navbar';
import LeagueFilter from './components/LeagueFilter';
import MatchCard from './components/MatchCard';
import MatchModal from './components/MatchModal';
import ValueBetScanner from './components/ValueBetScanner';
import BacktestLab from './components/BacktestLab';
import { fetchPredictions } from './services/api';
import { AlertTriangle, RefreshCw } from 'lucide-react';

export default function App() {
  const [activeTab, setActiveTab] = useState('predictions');
  const [selectedLeague, setSelectedLeague] = useState('ALL');
  const [predictions, setPredictions] = useState([]);
  const [selectedMatch, setSelectedMatch] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    loadPredictions();
  }, [selectedLeague]);

  async function loadPredictions() {
    setLoading(true);
    setError(null);
    try {
      const data = await fetchPredictions(selectedLeague);
      setPredictions(data);
    } catch (err) {
      console.error(err);
      setError(err.message || "Failed to load match predictions");
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="min-h-screen bg-[#0B0F19] text-slate-100 flex flex-col font-sans">
      <Navbar activeTab={activeTab} setActiveTab={setActiveTab} />

      <main className="flex-1 max-w-7xl w-full mx-auto px-4 sm:px-6 lg:px-8 py-6">
        {activeTab === 'predictions' && (
          <div className="space-y-6">
            <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
              <div>
                <h2 className="text-lg font-bold text-white tracking-tight">Statistical Match Forecasts</h2>
                <p className="text-xs text-slate-400">Dixon-Coles bivariate Poisson modeling, expected goals (xG), and fair market pricing.</p>
              </div>
              <LeagueFilter selectedLeague={selectedLeague} onSelectLeague={setSelectedLeague} />
            </div>

            {/* Error Alert */}
            {error && (
              <div className="bg-red-500/10 border border-red-500/30 text-red-400 p-4 rounded-xl text-sm flex items-center justify-between">
                <div className="flex items-center gap-2">
                  <AlertTriangle className="h-5 w-5 flex-shrink-0" />
                  <span>{error}</span>
                </div>
                <button
                  onClick={loadPredictions}
                  className="flex items-center gap-1.5 px-3 py-1 bg-red-500/20 hover:bg-red-500/30 text-red-300 rounded text-xs font-medium transition-colors"
                >
                  <RefreshCw className="h-3.5 w-3.5" /> Retry
                </button>
              </div>
            )}

            {loading ? (
              <div className="text-center py-24 text-slate-400 text-sm flex flex-col items-center justify-center space-y-2">
                <div className="h-6 w-6 border-2 border-emerald-500 border-t-transparent rounded-full animate-spin"></div>
                <span>Computing bivariate probability distributions...</span>
              </div>
            ) : error ? null : predictions.length === 0 ? (
              <div className="text-center py-20 text-slate-500 text-sm">
                No scheduled matches found for this competition.
              </div>
            ) : (
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-5">
                {predictions.map(item => (
                  <MatchCard key={item.id} item={item} onSelectMatch={setSelectedMatch} />
                ))}
              </div>
            )}
          </div>
        )}

        {activeTab === 'value-scanner' && <ValueBetScanner />}

        {activeTab === 'backtest' && <BacktestLab />}
      </main>

      {selectedMatch && (
        <MatchModal item={selectedMatch} onClose={() => setSelectedMatch(null)} />
      )}
    </div>
  );
}
