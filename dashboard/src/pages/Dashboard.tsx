import React, { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import { getHealth, getFeedbackStats, getMetrics, getUsage, type UsageResponse } from '../services/api';
import { Shield, Activity, AlertTriangle, CheckCircle, Clock, TrendingUp, Zap, DollarSign, Cpu } from 'lucide-react';

interface Stats {
  analyzeRequests: number;
  totalDetections: number;
  detectionRate: number;
  feedbackPending: number;
}

const Dashboard: React.FC = () => {
  const [apiStatus, setApiStatus] = useState<'online' | 'offline' | 'checking'>('checking');
  const [stats, setStats] = useState<Stats>({ analyzeRequests: 0, totalDetections: 0, detectionRate: 0, feedbackPending: 0 });
  const [feedbackStats, setFeedbackStats] = useState<any>(null);
  const [usage, setUsage] = useState<UsageResponse | null>(null);

  useEffect(() => {
    const checkHealth = async () => {
      try {
        await getHealth();
        setApiStatus('online');
      } catch {
        setApiStatus('offline');
      }
    };

    const fetchStats = async () => {
      try {
        const metrics = await getMetrics();
        let analyzeRequests = 0;
        let totalDetections = 0;
        
        const lines = metrics.split('\n');
        lines.forEach((line: string) => {
          const reqMatch = line.match(/restrictor_requests_total\{endpoint="\/analyze",method="POST"[^}]*\}\s+([\d.]+)/);
          if (reqMatch && !line.includes('_created')) {
            analyzeRequests += parseFloat(reqMatch[1]);
          }
          const detMatch = line.match(/restrictor_detections_total\{[^}]*\}\s+([\d.]+)/);
          if (detMatch && !line.includes('_created')) {
            totalDetections += parseFloat(detMatch[1]);
          }
        });
        
        const detectionRate = analyzeRequests > 0 ? (totalDetections / analyzeRequests) * 100 : 0;
        setStats(prev => ({ ...prev, analyzeRequests, totalDetections, detectionRate }));
      } catch (e) {
        console.log('Metrics fetch failed');
      }

      try {
        const fb = await getFeedbackStats();
        setFeedbackStats(fb);
        setStats(prev => ({ ...prev, feedbackPending: fb.pending_review }));
      } catch (e) {
        console.log('Feedback stats failed');
      }

      try {
        const usageData = await getUsage();
        setUsage(usageData);
      } catch (e) {
        console.log('Usage fetch failed');
      }
    };

    checkHealth();
    fetchStats();
    const interval = setInterval(() => { checkHealth(); fetchStats(); }, 30000);
    return () => clearInterval(interval);
  }, []);

  const statCards = [
    { label: 'Analyze Requests', value: Math.round(stats.analyzeRequests), icon: Activity, color: 'blue' },
    { label: 'Detections', value: Math.round(stats.totalDetections), icon: AlertTriangle, color: 'yellow' },
    { label: 'Detection Rate', value: `${stats.detectionRate.toFixed(1)}%`, icon: TrendingUp, color: 'purple' },
    { label: 'Pending Review', value: stats.feedbackPending, icon: Clock, color: 'orange' },
  ];

  return (
    <div className="p-8">
      <div className="flex items-center justify-between mb-8">
        <div>
          <h1 className="text-2xl font-bold mb-1">Dashboard</h1>
          <p className="text-gray-400">Overview of your content moderation system</p>
        </div>
        <div className={`flex items-center gap-2 px-4 py-2 rounded-full glass ${apiStatus === 'online' ? 'border border-green-500/50' : 'border border-red-500/50'}`}>
          <span className={`w-2 h-2 rounded-full pulse-dot ${apiStatus === 'online' ? 'bg-green-500' : 'bg-red-500'}`} />
          <span className="text-sm">{apiStatus === 'online' ? 'API Online' : 'API Offline'}</span>
        </div>
      </div>

      <div className="grid grid-cols-4 gap-6 mb-8">
        {statCards.map((stat, i) => {
          const Icon = stat.icon;
          return (
            <div key={i} className="glass rounded-2xl p-6">
              <div className="flex items-center justify-between mb-4">
                <div className={`p-3 rounded-xl bg-${stat.color}-500/20`}>
                  <Icon className={`w-6 h-6 text-${stat.color}-400`} />
                </div>
              </div>
              <p className={`text-3xl font-bold text-${stat.color}-400 mb-1`}>{stat.value}</p>
              <p className="text-sm text-gray-400">{stat.label}</p>
            </div>
          );
        })}
      </div>

      {/* Claude Usage Card */}
      {usage && (
        <div className="glass rounded-2xl p-6 mb-8">
          <div className="flex items-center gap-3 mb-4">
            <div className="p-3 rounded-xl bg-purple-500/20">
              <Cpu className="w-6 h-6 text-purple-400" />
            </div>
            <div>
              <h3 className="font-semibold">Claude API Usage</h3>
              <p className="text-sm text-gray-400">Real-time token and cost tracking</p>
            </div>
          </div>
          <div className="grid grid-cols-5 gap-4">
            <div className="text-center p-4 rounded-xl bg-dark-800/50">
              <p className="text-2xl font-bold text-blue-400">{usage.total_requests}</p>
              <p className="text-xs text-gray-400">Total Calls</p>
            </div>
            <div className="text-center p-4 rounded-xl bg-dark-800/50">
              <p className="text-2xl font-bold text-green-400">{usage.total_tokens.toLocaleString()}</p>
              <p className="text-xs text-gray-400">Total Tokens</p>
            </div>
            <div className="text-center p-4 rounded-xl bg-dark-800/50">
              <p className="text-2xl font-bold text-yellow-400">${usage.total_cost_usd.toFixed(4)}</p>
              <p className="text-xs text-gray-400">Total Cost</p>
            </div>
            <div className="text-center p-4 rounded-xl bg-dark-800/50">
              <p className="text-2xl font-bold text-orange-400">${usage.daily_cost_usd.toFixed(4)}</p>
              <p className="text-xs text-gray-400">Today's Cost</p>
            </div>
            <div className="text-center p-4 rounded-xl bg-dark-800/50">
              <p className="text-2xl font-bold text-purple-400">${usage.remaining_daily_budget.toFixed(2)}</p>
              <p className="text-xs text-gray-400">Budget Left</p>
            </div>
          </div>
          <div className="mt-4 flex items-center justify-between text-sm">
            <span className="text-gray-400">Daily Cap: ${usage.daily_cap_usd}</span>
            <span className="text-gray-400">Rate Limit: {usage.requests_per_minute_limit}/min</span>
            <div className="flex items-center gap-2">
              <span className="text-gray-400">Budget Used:</span>
              <div className="w-32 h-2 bg-dark-600 rounded-full overflow-hidden">
                <div 
                  className="h-full bg-gradient-to-r from-green-500 to-yellow-500 rounded-full"
                  style={{ width: `${Math.min((usage.daily_cost_usd / usage.daily_cap_usd) * 100, 100)}%` }}
                />
              </div>
              <span className="text-gray-400">{((usage.daily_cost_usd / usage.daily_cap_usd) * 100).toFixed(1)}%</span>
            </div>
          </div>
        </div>
      )}

      <div className="grid grid-cols-2 gap-6 mb-8">
        <div className="glass rounded-2xl p-6">
          <h3 className="font-semibold mb-4">Quick Actions</h3>
          <div className="grid grid-cols-2 gap-3">
            <Link to="/analyze" className="p-4 rounded-xl bg-blue-500/10 border border-blue-500/20 hover:bg-blue-500/20 transition">
              <Zap className="w-6 h-6 text-blue-400 mb-2" />
              <p className="font-medium">Analyze Text</p>
              <p className="text-xs text-gray-400">Test content moderation</p>
            </Link>
            <Link to="/feedback" className="p-4 rounded-xl bg-yellow-500/10 border border-yellow-500/20 hover:bg-yellow-500/20 transition">
              <AlertTriangle className="w-6 h-6 text-yellow-400 mb-2" />
              <p className="font-medium">Review Feedback</p>
              <p className="text-xs text-gray-400">{stats.feedbackPending} pending</p>
            </Link>
            <Link to="/learning" className="p-4 rounded-xl bg-purple-500/10 border border-purple-500/20 hover:bg-purple-500/20 transition">
              <Activity className="w-6 h-6 text-purple-400 mb-2" />
              <p className="font-medium">Active Learning</p>
              <p className="text-xs text-gray-400">Train from feedback</p>
            </Link>
            <a href="http://localhost:3001" target="_blank" rel="noreferrer" className="p-4 rounded-xl bg-green-500/10 border border-green-500/20 hover:bg-green-500/20 transition">
              <TrendingUp className="w-6 h-6 text-green-400 mb-2" />
              <p className="font-medium">Grafana</p>
              <p className="text-xs text-gray-400">View metrics</p>
            </a>
          </div>
        </div>

        <div className="glass rounded-2xl p-6">
          <h3 className="font-semibold mb-4">Detection Pipeline</h3>
          <div className="space-y-3">
            <div className="flex items-center justify-between p-3 rounded-lg bg-dark-800/50">
              <div className="flex items-center gap-3">
                <CheckCircle className="w-5 h-5 text-green-400" />
                <span>Safe Phrases</span>
              </div>
              <span className="text-green-400 font-mono text-sm">&lt;1ms</span>
            </div>
            <div className="flex items-center justify-between p-3 rounded-lg bg-dark-800/50">
              <div className="flex items-center gap-3">
                <Shield className="w-5 h-5 text-blue-400" />
                <span>Keywords</span>
              </div>
              <span className="text-blue-400 font-mono text-sm">&lt;1ms</span>
            </div>
            <div className="flex items-center justify-between p-3 rounded-lg bg-dark-800/50">
              <div className="flex items-center gap-3">
                <Activity className="w-5 h-5 text-purple-400" />
                <span>MoE (MuRIL)</span>
              </div>
              <span className="text-purple-400 font-mono text-sm">~50ms</span>
            </div>
            <div className="flex items-center justify-between p-3 rounded-lg bg-dark-800/50">
              <div className="flex items-center gap-3">
                <Zap className="w-5 h-5 text-orange-400" />
                <span>Claude API</span>
              </div>
              <span className="text-orange-400 font-mono text-sm">~1-2s</span>
            </div>
          </div>
          <div className="mt-4 pt-4 border-t border-white/10 grid grid-cols-3 gap-4 text-center">
            <div>
              <p className="text-xl font-bold text-blue-400">96.1%</p>
              <p className="text-xs text-gray-400">F1 Score</p>
            </div>
            <div>
              <p className="text-xl font-bold text-green-400">95.9%</p>
              <p className="text-xs text-gray-400">Recall</p>
            </div>
            <div>
              <p className="text-xl font-bold text-purple-400">99%</p>
              <p className="text-xs text-gray-400">Hindi F1</p>
            </div>
          </div>
        </div>
      </div>

      {feedbackStats && (
        <div className="glass rounded-2xl p-6">
          <h3 className="font-semibold mb-4">Feedback Overview</h3>
          <div className="grid grid-cols-5 gap-4">
            <div className="text-center p-4 rounded-xl bg-dark-800/50">
              <p className="text-2xl font-bold text-white">{feedbackStats.total}</p>
              <p className="text-xs text-gray-400">Total</p>
            </div>
            <div className="text-center p-4 rounded-xl bg-dark-800/50">
              <p className="text-2xl font-bold text-green-400">{feedbackStats.by_type?.correct || 0}</p>
              <p className="text-xs text-gray-400">Correct</p>
            </div>
            <div className="text-center p-4 rounded-xl bg-dark-800/50">
              <p className="text-2xl font-bold text-red-400">{feedbackStats.by_type?.false_positive || 0}</p>
              <p className="text-xs text-gray-400">False Positive</p>
            </div>
            <div className="text-center p-4 rounded-xl bg-dark-800/50">
              <p className="text-2xl font-bold text-yellow-400">{feedbackStats.by_type?.false_negative || 0}</p>
              <p className="text-xs text-gray-400">False Negative</p>
            </div>
            <div className="text-center p-4 rounded-xl bg-dark-800/50">
              <p className="text-2xl font-bold text-blue-400">{feedbackStats.reviewed}</p>
              <p className="text-xs text-gray-400">Reviewed</p>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default Dashboard;
