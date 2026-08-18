import React, { useState, useEffect } from 'react';
import axios from 'axios';

const TradeHub = ({ socket }) => {
  const [teamId, setTeamId] = useState(1);
  const [trades, setTrades] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  useEffect(() => {
    fetchTradeRecommendations();
  }, [teamId]);

  const fetchTradeRecommendations = async () => {
    try {
      setLoading(true);
      const res = await axios.post('/api/trades/suggest', {
        team_id: teamId,
        current_lineup: [],
        available_players: [],
        top_n: 5,
      });
      setTrades(res.data.trades || []);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  const getStrengthColor = (strength) => {
    switch (strength) {
      case 'STRONG_BUY':
        return 'text-green-400';
      case 'BUY':
        return 'text-blue-400';
      case 'MODERATE':
        return 'text-yellow-400';
      default:
        return 'text-slate-400';
    }
  };

  return (
    <div className="space-y-6">
      <div className="bg-slate-800 border border-slate-700 rounded-lg p-6">
        <h1 className="text-3xl font-bold text-green-400 mb-4">💱 Trade Hub</h1>
        <p className="text-slate-400 mb-6">AI-powered trade recommendations to improve your team</p>

        <div className="flex gap-4">
          <select
            value={teamId}
            onChange={(e) => setTeamId(Number(e.target.value))}
            className="px-4 py-2 bg-slate-700 text-white rounded-lg border border-slate-600 focus:border-green-400 outline-none"
          >
            {Array.from({ length: 14 }, (_, i) => (
              <option key={i + 1} value={i + 1}>
                Team {i + 1}
              </option>
            ))}
          </select>
          <button
            onClick={fetchTradeRecommendations}
            disabled={loading}
            className="px-6 py-2 bg-green-500 text-black font-bold rounded-lg hover:bg-green-400 disabled:opacity-50 transition"
          >
            {loading ? 'Loading...' : '🔄 Refresh'}
          </button>
        </div>
      </div>

      {error && <div className="text-red-400 bg-red-400/10 p-4 rounded-lg border border-red-400">{error}</div>}

      {trades.length === 0 ? (
        <div className="bg-slate-800 border border-slate-700 rounded-lg p-12 text-center">
          <p className="text-slate-400">No trade recommendations available at this time</p>
        </div>
      ) : (
        <div className="grid grid-cols-1 gap-4">
          {trades.map((trade, idx) => (
            <div key={idx} className="bg-slate-800 border border-slate-700 rounded-lg p-6 hover:border-green-400/50 transition">
              <div className="flex items-center justify-between mb-4">
                <div className="flex items-center gap-4">
                  <div>
                    <p className="text-slate-400 text-sm">Give</p>
                    <p className="text-lg font-bold text-red-400">{trade.trade_out.name}</p>
                    <p className="text-xs text-slate-500">{trade.trade_out.position}</p>
                  </div>
                  <p className="text-2xl text-slate-400">→</p>
                  <div>
                    <p className="text-slate-400 text-sm">Get</p>
                    <p className="text-lg font-bold text-green-400">{trade.trade_in.name}</p>
                    <p className="text-xs text-slate-500">{trade.trade_in.position}</p>
                  </div>
                </div>
                <div className="text-right">
                  <p className={`text-lg font-bold ${getStrengthColor(trade.strength)}`}>
                    {trade.strength}
                  </p>
                  <p className="text-green-400 text-sm">+{trade.expected_point_gain.toFixed(1)} pts</p>
                </div>
              </div>
              <div className="flex justify-between text-xs text-slate-400 pt-4 border-t border-slate-700">
                <span>Salary Impact: ${(trade.salary_impact / 1000).toFixed(0)}k</span>
                <button className="text-green-400 hover:text-green-300">Review Trade →</button>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
};

export default TradeHub;
