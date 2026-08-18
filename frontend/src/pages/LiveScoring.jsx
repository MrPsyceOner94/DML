import React, { useEffect, useState } from 'react';

const LiveScoring = ({ socket }) => {
  const [matches, setMatches] = useState([]);
  const [scores, setScores] = useState({});
  const [isConnected, setIsConnected] = useState(false);

  useEffect(() => {
    if (!socket) return;

    // Connect to live scoring WebSocket
    socket.emit('subscribe', { channel: 'live-scoring' });

    socket.on('connect', () => {
      setIsConnected(true);
      console.log('Connected to live scoring');
    });

    socket.on('score_update', (data) => {
      setScores((prev) => ({
        ...prev,
        [data.player_id]: data.score,
      }));
    });

    socket.on('disconnect', () => {
      setIsConnected(false);
    });

    return () => {
      socket.emit('unsubscribe', { channel: 'live-scoring' });
    };
  }, [socket]);

  useEffect(() => {
    // Fetch initial matches
    const fetchMatches = async () => {
      try {
        const res = await fetch('/api/fixtures?round=24');
        const data = await res.json();
        setMatches(data);
      } catch (err) {
        console.error('Error fetching matches:', err);
      }
    };

    fetchMatches();
  }, []);

  return (
    <div className="space-y-6">
      <div className="bg-slate-800 border border-slate-700 rounded-lg p-6">
        <div className="flex items-center justify-between mb-4">
          <h1 className="text-3xl font-bold text-green-400">📈 Live Scoring</h1>
          <div className="flex items-center gap-2">
            <div className={`w-3 h-3 rounded-full ${isConnected ? 'bg-green-400 animate-pulse' : 'bg-red-400'}`}></div>
            <span className="text-sm text-slate-400">{isConnected ? 'Live' : 'Offline'}</span>
          </div>
        </div>
        <p className="text-slate-400">Real-time player performance and match updates</p>
      </div>

      <div className="grid grid-cols-1 gap-6">
        {matches.map((match, idx) => (
          <div key={idx} className="bg-slate-800 border border-slate-700 rounded-lg p-6">
            <div className="flex items-center justify-around mb-6">
              <div className="text-center">
                <p className="text-slate-400 text-sm mb-2">Home Team</p>
                <p className="text-2xl font-bold text-white">Team A</p>
              </div>
              <div className="text-center">
                <p className="text-4xl font-bold text-green-400">VS</p>
              </div>
              <div className="text-center">
                <p className="text-slate-400 text-sm mb-2">Away Team</p>
                <p className="text-2xl font-bold text-white">Team B</p>
              </div>
            </div>

            <div className="bg-slate-700/50 p-4 rounded-lg border border-slate-600 text-center">
              <p className="text-slate-400 text-sm mb-2">Current Status</p>
              <p className="text-xl font-bold text-yellow-400">Q2 - 25 mins</p>
            </div>
          </div>
        ))}
      </div>

      <div className="bg-slate-800 border border-slate-700 rounded-lg p-6">
        <h2 className="text-xl font-bold text-white mb-4">Top Scorers This Round</h2>
        <div className="space-y-3">
          {[
            { name: 'Player Name', score: 45.5 },
            { name: 'Another Player', score: 42.0 },
            { name: 'Third Player', score: 38.5 },
          ].map((player, idx) => (
            <div key={idx} className="flex items-center justify-between p-3 bg-slate-700/50 rounded-lg border border-slate-600">
              <span className="text-white font-medium">{player.name}</span>
              <span className="text-green-400 font-bold">{player.score} pts</span>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
};

export default LiveScoring;
