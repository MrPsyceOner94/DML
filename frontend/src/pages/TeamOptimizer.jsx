import React, { useState, useEffect } from 'react';
import axios from 'axios';

const TeamOptimizer = ({ socket }) => {
  const [teamId, setTeamId] = useState(1);
  const [lineup, setLineup] = useState([]);
  const [optimizedLineup, setOptimizedLineup] = useState([]);
  const [salaryInfo, setSalaryInfo] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  useEffect(() => {
    fetchTeamData();
  }, [teamId]);

  const fetchTeamData = async () => {
    try {
      setLoading(true);
      const res = await axios.get(`/api/teams/${teamId}`);
      // Extract players from team data
      setLineup(res.data.squad || []);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  const optimizeTeam = async () => {
    try {
      setLoading(true);
      const res = await axios.post('/api/optimize/team', {
        team_id: teamId,
        available_players: lineup,
        current_lineup: lineup,
      });
      setOptimizedLineup(res.data.lineup);
      setSalaryInfo({
        total: res.data.total_salary,
        remaining: res.data.salary_remaining,
        predicted_score: res.data.total_predicted_score,
        confidence: res.data.confidence,
      });
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="space-y-6">
      <div className="bg-slate-800 border border-slate-700 rounded-lg p-6">
        <h1 className="text-3xl font-bold text-green-400 mb-4">⚙️ Team Optimizer</h1>
        <p className="text-slate-400 mb-6">Maximize your fantasy points within salary cap constraints</p>

        <div className="flex gap-4 mb-6">
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
            onClick={optimizeTeam}
            disabled={loading}
            className="px-6 py-2 bg-green-500 text-black font-bold rounded-lg hover:bg-green-400 disabled:opacity-50 transition"
          >
            {loading ? 'Optimizing...' : '🚀 Optimize'}
          </button>
        </div>

        {error && <div className="text-red-400 mb-4">Error: {error}</div>}

        {salaryInfo && (
          <div className="grid grid-cols-4 gap-4 mb-6">
            <div className="bg-slate-700/50 p-4 rounded-lg border border-slate-600">
              <p className="text-slate-400 text-sm">Total Salary Used</p>
              <p className="text-2xl font-bold text-green-400">${(salaryInfo.total / 1000000).toFixed(1)}M</p>
            </div>
            <div className="bg-slate-700/50 p-4 rounded-lg border border-slate-600">
              <p className="text-slate-400 text-sm">Remaining</p>
              <p className="text-2xl font-bold text-blue-400">${(salaryInfo.remaining / 1000000).toFixed(2)}M</p>
            </div>
            <div className="bg-slate-700/50 p-4 rounded-lg border border-slate-600">
              <p className="text-slate-400 text-sm">Predicted Score</p>
              <p className="text-2xl font-bold text-yellow-400">{salaryInfo.predicted_score.toFixed(0)}</p>
            </div>
            <div className="bg-slate-700/50 p-4 rounded-lg border border-slate-600">
              <p className="text-slate-400 text-sm">Confidence</p>
              <p className="text-2xl font-bold text-purple-400">{(salaryInfo.confidence * 100).toFixed(0)}%</p>
            </div>
          </div>
        )}
      </div>

      {optimizedLineup.length > 0 && (
        <div className="bg-slate-800 border border-slate-700 rounded-lg p-6">
          <h2 className="text-xl font-bold text-white mb-4">Optimized Lineup</h2>
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b border-slate-700">
                  <th className="text-left p-3 text-slate-400">Player</th>
                  <th className="text-left p-3 text-slate-400">Position</th>
                  <th className="text-right p-3 text-slate-400">Salary</th>
                  <th className="text-right p-3 text-slate-400">Predicted</th>
                </tr>
              </thead>
              <tbody>
                {optimizedLineup.map((player, idx) => (
                  <tr key={idx} className="border-b border-slate-700 hover:bg-slate-700/50">
                    <td className="p-3 font-medium text-white">{player.name}</td>
                    <td className="p-3 text-slate-300">{player.position}</td>
                    <td className="text-right p-3 text-slate-300">${(player.salary / 1000000).toFixed(2)}M</td>
                    <td className="text-right p-3 font-medium text-green-400">{player.predicted_score.toFixed(1)}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}
    </div>
  );
};

export default TeamOptimizer;
