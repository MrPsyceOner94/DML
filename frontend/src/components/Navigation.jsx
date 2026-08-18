import React from 'react';
import clsx from 'clsx';

const Navigation = ({ currentPage, onPageChange }) => {
  const pages = [
    { id: 'dashboard', label: '📊 Dashboard', icon: '📊' },
    { id: 'optimizer', label: '⚙️ Team Optimizer', icon: '⚙️' },
    { id: 'scoring', label: '📈 Live Scoring', icon: '📈' },
    { id: 'trades', label: '💱 Trade Hub', icon: '💱' },
    { id: 'chat', label: '💬 Coaches Chat', icon: '💬' },
    { id: 'alerts', label: '🚨 Alerts', icon: '🚨' },
  ];

  return (
    <nav className="fixed left-0 top-0 w-64 h-screen bg-slate-950 border-r border-slate-700 p-6 overflow-y-auto">
      <div className="mb-8">
        <h1 className="text-2xl font-bold text-green-400 mb-1">DML</h1>
        <p className="text-xs text-slate-500 uppercase tracking-wider">NRL Fantasy 2026</p>
      </div>

      <div className="space-y-2">
        {pages.map((page) => (
          <button
            key={page.id}
            onClick={() => onPageChange(page.id)}
            className={clsx(
              'w-full text-left px-4 py-3 rounded-lg transition-all duration-200 font-medium',
              currentPage === page.id
                ? 'bg-green-500/20 text-green-400 border border-green-400/50'
                : 'text-slate-300 hover:bg-slate-800 hover:text-white border border-transparent'
            )}
          >
            <span className="mr-2">{page.icon}</span>
            {page.label}
          </button>
        ))}
      </div>

      <div className="mt-12 pt-6 border-t border-slate-700">
        <p className="text-xs text-slate-500 mb-4">QUICK LINKS</p>
        <button className="w-full text-left px-4 py-2 text-sm text-slate-400 hover:text-white transition">
          API Docs
        </button>
        <button className="w-full text-left px-4 py-2 text-sm text-slate-400 hover:text-white transition">
          Settings
        </button>
      </div>
    </nav>
  );
};

export default Navigation;
