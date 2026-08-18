import React, { useEffect, useState } from 'react';
import { useDispatch, useSelector } from 'react-redux';
import io from 'socket.io-client';
import Dashboard from './pages/Dashboard';
import TeamOptimizer from './pages/TeamOptimizer';
import LiveScoring from './pages/LiveScoring';
import TradeHub from './pages/TradeHub';
import CoachesChat from './pages/CoachesChat';
import AlertCenter from './pages/AlertCenter';
import Navigation from './components/Navigation';

const App = () => {
  const [currentPage, setCurrentPage] = useState('dashboard');
  const [socket, setSocket] = useState(null);
  const [isAuthenticated, setIsAuthenticated] = useState(false);
  const dispatch = useDispatch();

  useEffect(() => {
    // Initialize WebSocket connection
    const newSocket = io(process.env.REACT_APP_API_URL || 'http://localhost:8000');
    setSocket(newSocket);

    // Listen for connection events
    newSocket.on('connect', () => {
      console.log('Connected to server');
    });

    newSocket.on('disconnect', () => {
      console.log('Disconnected from server');
    });

    return () => newSocket.close();
  }, []);

  const renderPage = () => {
    switch (currentPage) {
      case 'dashboard':
        return <Dashboard />;
      case 'optimizer':
        return <TeamOptimizer socket={socket} />;
      case 'scoring':
        return <LiveScoring socket={socket} />;
      case 'trades':
        return <TradeHub socket={socket} />;
      case 'chat':
        return <CoachesChat socket={socket} />;
      case 'alerts':
        return <AlertCenter socket={socket} />;
      default:
        return <Dashboard />;
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-900 via-slate-800 to-slate-900">
      <Navigation currentPage={currentPage} onPageChange={setCurrentPage} />
      <main className="ml-64 p-8">
        <div className="max-w-7xl mx-auto">
          {renderPage()}
        </div>
      </main>
    </div>
  );
};

export default App;
