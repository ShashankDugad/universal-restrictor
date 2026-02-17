import React, { useState } from 'react';
import { useAuth } from '../contexts/AuthContext';
import { Key, Save, Shield, RefreshCw, Database } from 'lucide-react';

const Settings: React.FC = () => {
  const { apiKey, tenant, tier } = useAuth();
  const [newApiKey, setNewApiKey] = useState(apiKey);
  const [saved, setSaved] = useState(false);

  const handleSave = () => {
    localStorage.setItem('apiKey', newApiKey);
    setSaved(true);
    setTimeout(() => setSaved(false), 2000);
  };

  const links = [
    { href: 'http://localhost:8000/docs', title: 'API Documentation', desc: 'Swagger UI' },
    { href: 'http://localhost:9090', title: 'Prometheus', desc: 'Metrics and Queries' },
    { href: 'http://localhost:3001', title: 'Grafana', desc: 'Dashboards' },
    { href: 'http://localhost:8000/metrics', title: 'Raw Metrics', desc: 'Prometheus Format' },
  ];

  return (
    <div className="p-8">
      <div className="mb-8">
        <h1 className="text-2xl font-bold mb-1">Settings</h1>
        <p className="text-gray-400">Manage your API configuration and preferences</p>
      </div>

      <div className="max-w-2xl space-y-6">
        <div className="glass rounded-2xl p-6">
          <div className="flex items-center gap-3 mb-6">
            <div className="p-3 rounded-xl bg-blue-500/20">
              <Shield className="w-6 h-6 text-blue-400" />
            </div>
            <div>
              <h3 className="font-semibold">Account Information</h3>
              <p className="text-sm text-gray-400">Your current subscription details</p>
            </div>
          </div>
          <div className="grid grid-cols-2 gap-4">
            <div className="p-4 rounded-xl bg-dark-800/50">
              <p className="text-xs text-gray-500 mb-1">Tenant ID</p>
              <p className="font-mono">{tenant}</p>
            </div>
            <div className="p-4 rounded-xl bg-dark-800/50">
              <p className="text-xs text-gray-500 mb-1">Subscription Tier</p>
              <span className={`inline-flex px-3 py-1 rounded-full text-sm ${
                tier === 'enterprise' ? 'bg-purple-500/20 text-purple-400' :
                tier === 'pro' ? 'bg-blue-500/20 text-blue-400' :
                'bg-gray-500/20 text-gray-400'
              }`}>
                {tier?.toUpperCase()}
              </span>
            </div>
          </div>
        </div>

        <div className="glass rounded-2xl p-6">
          <div className="flex items-center gap-3 mb-6">
            <div className="p-3 rounded-xl bg-yellow-500/20">
              <Key className="w-6 h-6 text-yellow-400" />
            </div>
            <div>
              <h3 className="font-semibold">API Key</h3>
              <p className="text-sm text-gray-400">Your authentication key</p>
            </div>
          </div>
          <div className="space-y-4">
            <input
              type="password"
              value={newApiKey}
              onChange={(e) => setNewApiKey(e.target.value)}
              className="w-full px-4 py-3 bg-dark-800 rounded-xl border border-white/10 focus:border-blue-500 focus:outline-none font-mono"
            />
            <button
              onClick={handleSave}
              className="flex items-center gap-2 px-4 py-2 bg-blue-500/20 text-blue-400 rounded-xl hover:bg-blue-500/30"
            >
              <Save className="w-4 h-4" />
              {saved ? 'Saved!' : 'Save Changes'}
            </button>
          </div>
        </div>

        <div className="glass rounded-2xl p-6">
          <div className="flex items-center gap-3 mb-6">
            <div className="p-3 rounded-xl bg-green-500/20">
              <RefreshCw className="w-6 h-6 text-green-400" />
            </div>
            <div>
              <h3 className="font-semibold">Rate Limits</h3>
              <p className="text-sm text-gray-400">Your current usage limits</p>
            </div>
          </div>
          <div className="space-y-3">
            <div className="flex justify-between p-3 rounded-lg bg-dark-800/50">
              <span className="text-gray-400">Requests per minute</span>
              <span className="font-mono">{tier === 'enterprise' ? '6,000' : tier === 'pro' ? '600' : '60'}</span>
            </div>
            <div className="flex justify-between p-3 rounded-lg bg-dark-800/50">
              <span className="text-gray-400">Requests per day</span>
              <span className="font-mono">{tier === 'enterprise' ? 'Unlimited' : tier === 'pro' ? '50,000' : '1,000'}</span>
            </div>
          </div>
        </div>

        <div className="glass rounded-2xl p-6">
          <div className="flex items-center gap-3 mb-6">
            <div className="p-3 rounded-xl bg-purple-500/20">
              <Database className="w-6 h-6 text-purple-400" />
            </div>
            <div>
              <h3 className="font-semibold">External Services</h3>
              <p className="text-sm text-gray-400">Links to monitoring</p>
            </div>
          </div>
          <div className="grid grid-cols-2 gap-3">
            {links.map((link, i) => (
              <a key={i} href={link.href} target="_blank" rel="noreferrer" className="p-4 rounded-xl bg-dark-800/50 hover:bg-dark-700/50 text-center">
                <p className="font-medium">{link.title}</p>
                <p className="text-xs text-gray-400">{link.desc}</p>
              </a>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
};

export default Settings;
