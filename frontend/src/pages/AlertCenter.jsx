import React, { useState, useEffect } from 'react';
import axios from 'axios';

const AlertCenter = ({ socket }) => {
  const [teamId, setTeamId] = useState(1);
  const [alerts, setAlerts] = useState([]);
  const [filter, setFilter] = useState('all');
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    fetchAlerts();
  }, [teamId, filter]);

  useEffect(() => {
    if (!socket) return;

    socket.on(`alerts-${teamId}`, (alert) => {
      setAlerts((prev) => [alert, ...prev]);
    });

    return () => {
      socket.off(`alerts-${teamId}`);
    };
  }, [socket, teamId]);

  const fetchAlerts = async () => {
    try {
      setLoading(true);
      const params = new URLSearchParams();
      if (filter !== 'all') params.append('alert_type', filter);

      const res = await axios.get(`/api/alerts/?team_id=${teamId}&${params}`);
      setAlerts(res.data.alerts || []);
    } catch (err) {
      console.error('Error fetching alerts:', err);
    } finally {
      setLoading(false);
    }
  };

  const dismissAlert = async (alertId) => {
    try {
      await axios.delete(`/api/alerts/${alertId}?team_id=${teamId}`);
      setAlerts((prev) => prev.filter((a) => a.id !== alertId));
    } catch (err) {
      console.error('Error dismissing alert:', err);
    }
  };

  const getAlertColor = (severity) => {
    switch (severity) {
      case 'critical':
        return 'border-red-500 bg-red-500/10';
      case 'high':
        return 'border-orange-500 bg-orange-500/10';
      case 'medium':
        return 'border-yellow-500 bg-yellow-500/10';
      default:
        return 'border-blue-500 bg-blue-500/10';
    }
  };

  const getSeverityIcon = (severity) => {
    switch (severity) {
      case 'critical':
        return '🚨';
      case 'high':
        return '⚠️';
      case 'medium':
        return 'ℹ️';
      default:
        return '📢';
    }
  };

  return (
    <div className="space-y-6">
      <div className="bg-slate-800 border border-slate-700 rounded-lg p-6">
        <h1 className="text-3xl font-bold text-green-400 mb-4">🚨 Alert Center</h1>
        <p className="text-slate-400 mb-6">Stay informed with real-time injury, suspension, and trade alerts</p>

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
          <select
            value={filter}
            onChange={(e) => setFilter(e.target.value)}
            className="px-4 py-2 bg-slate-700 text-white rounded-lg border border-slate-600 focus:border-green-400 outline-none"
          >
            <option value="all">All Alerts</option>
            <option value="injury">Injuries</option>
            <option value="suspension">Suspensions</option>
            <option value="trade_opportunity">Trade Opportunities</option>
            <option value="lineup_lock">Lineup Lock</option>
          </select>
          <button
            onClick={fetchAlerts}
            disabled={loading}
            className="px-6 py-2 bg-green-500 text-black font-bold rounded-lg hover:bg-green-400 disabled:opacity-50 transition"
          >
            {loading ? 'Refreshing...' : '🔄 Refresh'}
          </button>
        </div>
      </div>

      {alerts.length === 0 ? (
        <div className="bg-slate-800 border border-slate-700 rounded-lg p-12 text-center">
          <p className="text-slate-400">✓ All clear! No active alerts</p>
        </div>
      ) : (
        <div className="space-y-3">
          {alerts.map((alert) => (
            <div key={alert.id} className={`border rounded-lg p-4 ${getAlertColor(alert.severity)}`}>
              <div className="flex items-start justify-between">
                <div className="flex gap-3 flex-1">
                  <span className="text-2xl">{getSeverityIcon(alert.severity)}</span>
                  <div>
                    <h3 className="font-bold text-white">{alert.title}</h3>
                    <p className="text-sm text-slate-300 mt-1">{alert.message}</p>
                    <p className="text-xs text-slate-500 mt-2">
                      {new Date(alert.created_at).toLocaleString()}
                    </p>
                  </div>
                </div>
                <button
                  onClick={() => dismissAlert(alert.id)}
                  className="text-slate-400 hover:text-white transition ml-4 flex-shrink-0"
                >
                  ✕
                </button>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
};

export default AlertCenter;
