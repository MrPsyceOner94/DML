import React, { useEffect, useState } from 'react';
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts';
import axios from 'axios';

const Dashboard = () => {
  const [league, setLeague] = useState(null);
  const [standings, setStandings] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    const fetchData = async () => {
      try {
        const [leagueRes, standingsRes] = await Promise.all([
          axios.get('/api/league'),
          axios.get('/api/standings?round=23'),
        ]);
        setLeague(leagueRes.data);
        setStandings(standingsRes.data);
      } catch (err) {
        setError(err.message);
      } finally {
        setLoading(false);
      }
    };

    fetchData();
  }, []);

  if (loading) {
    return (
      <div className="flex items-center justify-center h-96">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-green-400"></div>
      </div>
    );
  }

  if (error) {
    return <div className="text-red-400">Error: {error}</div>;
  }

  const topTeams = standings.slice(0, 8);

  return (
    <div className="space-y-8">
      <div className="bg-slate-800 border border-slate-700 rounded-lg p-6">
        <h1 className="text-4xl font-bold text-green-400 mb-2">DML Draft Premiership 2026</h1>
        <p className="text-slate-400">Decision Making Layer for NRL Fantasy</p>
      </div>

      {/* Key Metrics */}
      <div className="grid grid-cols-4 gap-4">
        <div className="bg-slate-800 border border-slate-700 rounded-lg p-6">
          <p className="text-slate-400 text-sm">Teams</p>
          <p className="text-3xl font-bold text-green-400">{league?.teams?.length || 14}</p>
        </div>
        <div className="bg-slate-800 border border-slate-700 rounded-lg p-6">
          <p className="text-slate-400 text-sm">Rounds</p>
          <p className="text-3xl font-bold text-green-400">27</p>
        </div>
        <div className="bg-slate-800 border border-slate-700 rounded-lg p-6">
          <p className="text-slate-400 text-sm">Players</p>
          <p className="text-3xl font-bold text-green-400">{league?.player_ids?.length || 285}</p>
        </div>
        <div className="bg-slate-800 border border-slate-700 rounded-lg p-6">
          <p className="text-slate-400 text-sm">Status</p>
          <p className="text-3xl font-bold text-green-400">🟢 Live</p>
        </div>
      </div>

      {/* Ladder */}
      <div className="bg-slate-800 border border-slate-700 rounded-lg p-6">
        <h2 className="text-xl font-bold text-white mb-4">🏆 Competition Ladder</h2>
        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b border-slate-700">
                <th className="text-left p-3 text-slate-400">#</th>
                <th className="text-left p-3 text-slate-400">Team</th>
                <th className="text-right p-3 text-slate-400">H2H Pts</th>
                <th className="text-right p-3 text-slate-400">PF</th>
                <th className="text-right p-3 text-slate-400">PA</th>
                <th className="text-right p-3 text-slate-400">Diff</th>
              </tr>
            </thead>
            <tbody>
              {topTeams.map((team, idx) => (
                <tr key={idx} className="border-b border-slate-700 hover:bg-slate-700/50">
                  <td className="p-3 font-bold text-green-400">{team.rank}</td>
                  <td className="p-3 font-medium text-white">{team.name}</td>
                  <td className="text-right p-3 text-white">{team.league_points}</td>
                  <td className="text-right p-3 text-slate-300">{team.points_for}</td>
                  <td className="text-right p-3 text-slate-300">{team.points_against}</td>
                  <td className="text-right p-3 font-medium text-green-400">
                    {team.points_diff > 0 ? '+' : ''}{team.points_diff}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      {/* Charts */}
      <div className="grid grid-cols-2 gap-6">
        <div className="bg-slate-800 border border-slate-700 rounded-lg p-6">
          <h3 className="text-lg font-bold text-white mb-4">Points For Distribution</h3>
          <ResponsiveContainer width="100%" height={300}>
            <BarChart data={topTeams}>
              <CartesianGrid strokeDasharray="3 3" stroke="#334155" />
              <XAxis dataKey="name" stroke="#94a3b8" />
              <YAxis stroke="#94a3b8" />
              <Tooltip contentStyle={{ backgroundColor: '#1e293b', border: '1px solid #475569' }} />
              <Bar dataKey="points_for" fill="#10b981" />
            </BarChart>
          </ResponsiveContainer>
        </div>

        <div className="bg-slate-800 border border-slate-700 rounded-lg p-6">
          <h3 className="text-lg font-bold text-white mb-4">H2H Points Comparison</h3>
          <ResponsiveContainer width="100%" height={300}>
            <BarChart data={topTeams}>
              <CartesianGrid strokeDasharray="3 3" stroke="#334155" />
              <XAxis dataKey="name" stroke="#94a3b8" />
              <YAxis stroke="#94a3b8" />
              <Tooltip contentStyle={{ backgroundColor: '#1e293b', border: '1px solid #475569' }} />
              <Legend />
              <Bar dataKey="league_points" fill="#06b6d4" />
            </BarChart>
          </ResponsiveContainer>
        </div>
      </div>
    </div>
  );
};

export default Dashboard;
