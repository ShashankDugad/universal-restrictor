import React, { useState, useEffect } from 'react';
import { api, setApiKey, getApiKey, clearApiKey } from './api/client';
import Overview from './pages/Overview';
import TestAnalyze from './pages/TestAnalyze';
import Usage from './pages/Usage';
import Login from './pages/Login';

const tabs = [
  { id: 'overview', name: 'Overview', icon: '📊' },
  { id: 'test', name: 'Test Analyze', icon: '🧪' },
  { id: 'usage', name: 'API Usage', icon: '💰' },
];

function App() {
  const [isAuthenticated, setIsAuthenticated] = useState(false);
  const [activeTab, setActiveTab] = useState('overview');
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const key = getApiKey();
    if (key) {
      api.health()
        .then(() => setIsAuthenticated(true))
        .catch(() => clearApiKey())
        .finally(() => setLoading(false));
    } else {
      setLoading(false);
    }
  }, []);

  const handleLogin = (key) => {
    setApiKey(key);
    setIsAuthenticated(true);
  };

  const handleLogout = () => {
    clearApiKey();
    setIsAuthenticated(false);
  };

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gray-100">
        <div className="text-xl text-gray-600">Loading...</div>
      </div>
    );
  }

  if (!isAuthenticated) {
    return <Login onLogin={handleLogin} />;
  }

  return (
    <div className="min-h-screen bg-gray-100">
      {/* Header */}
      <header className="bg-white shadow">
        <div className="max-w-7xl mx-auto px-4 py-4 flex justify-between items-center">
          <div className="flex items-center space-x-3">
            <span className="text-2xl">🛡️</span>
            <h1 className="text-xl font-bold text-gray-900">Universal Restrictor</h1>
          </div>
          <button
            onClick={handleLogout}
            className="px-4 py-2 text-sm text-gray-600 hover:text-gray-900 hover:bg-gray-100 rounded"
          >
            Logout
          </button>
        </div>
      </header>

      {/* Navigation */}
      <nav className="bg-white border-b">
        <div className="max-w-7xl mx-auto px-4">
          <div className="flex space-x-8">
            {tabs.map((tab) => (
              <button
                key={tab.id}
                onClick={() => setActiveTab(tab.id)}
                className={`py-4 px-1 border-b-2 font-medium text-sm ${
                  activeTab === tab.id
                    ? 'border-blue-500 text-blue-600'
                    : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
                }`}
              >
                <span className="mr-2">{tab.icon}</span>
                {tab.name}
              </button>
            ))}
          </div>
        </div>
      </nav>

      {/* Content */}
      <main className="max-w-7xl mx-auto px-4 py-6">
        {activeTab === 'overview' && <Overview />}
        {activeTab === 'test' && <TestAnalyze />}
        {activeTab === 'usage' && <Usage />}
      </main>
    </div>
  );
}

export default App;
