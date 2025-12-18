import React, { useState, useEffect } from 'react';
import { api } from '../api/client';

function StatCard({ title, value, subtitle, icon, color }) {
  const colors = {
    blue: 'bg-blue-500',
    green: 'bg-green-500',
    yellow: 'bg-yellow-500',
    red: 'bg-red-500',
    purple: 'bg-purple-500',
  };

  return (
    <div className="bg-white rounded-lg shadow p-6">
      <div className="flex items-center">
        <div className={`${colors[color]} rounded-lg p-3 text-white text-2xl`}>
          {icon}
        </div>
        <div className="ml-4">
          <p className="text-sm font-medium text-gray-500">{title}</p>
          <p className="text-2xl font-semibold text-gray-900">{value}</p>
          {subtitle && <p className="text-sm text-gray-500">{subtitle}</p>}
        </div>
      </div>
    </div>
  );
}

function Overview() {
  const [stats, setStats] = useState(null);
  const [usage, setUsage] = useState(null);
  const [feedback, setFeedback] = useState(null);
  const [health, setHealth] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    const fetchData = async () => {
      try {
        const [healthData, usageData, feedbackData] = await Promise.all([
          api.health(),
          api.usage(),
          api.feedbackStats(),
        ]);
        setHealth(healthData);
        setUsage(usageData);
        setFeedback(feedbackData);
      } catch (err) {
        setError(err.message);
      } finally {
        setLoading(false);
      }
    };

    fetchData();
    const interval = setInterval(fetchData, 30000); // Refresh every 30s
    return () => clearInterval(interval);
  }, []);

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="text-gray-500">Loading dashboard...</div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded">
        Error loading dashboard: {error}
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Status Banner */}
      <div className={`rounded-lg p-4 ${health?.status === 'healthy' ? 'bg-green-50 border border-green-200' : 'bg-red-50 border border-red-200'}`}>
        <div className="flex items-center">
          <span className="text-2xl mr-3">{health?.status === 'healthy' ? '✅' : '❌'}</span>
          <div>
            <p className="font-medium text-gray-900">
              System Status: {health?.status === 'healthy' ? 'Healthy' : 'Unhealthy'}
            </p>
            <p className="text-sm text-gray-600">
              Version {health?.version} • Last updated: {new Date(health?.timestamp).toLocaleString()}
            </p>
          </div>
        </div>
      </div>

      {/* Stats Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        <StatCard
          title="Claude API Calls"
          value={usage?.total_requests || 0}
          subtitle={`${usage?.blocked_requests || 0} rate limited`}
          icon="🤖"
          color="blue"
        />
        <StatCard
          title="Total Cost"
          value={`$${(usage?.total_cost_usd || 0).toFixed(4)}`}
          subtitle={`Daily: $${(usage?.daily_cost_usd || 0).toFixed(4)}`}
          icon="💰"
          color="green"
        />
        <StatCard
          title="Input Tokens"
          value={(usage?.input_tokens || 0).toLocaleString()}
          icon="📥"
          color="purple"
        />
        <StatCard
          title="Output Tokens"
          value={(usage?.output_tokens || 0).toLocaleString()}
          icon="📤"
          color="yellow"
        />
      </div>

      {/* Feedback Stats */}
      <div className="bg-white rounded-lg shadow p-6">
        <h2 className="text-lg font-semibold text-gray-900 mb-4">Feedback Statistics</h2>
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          <div className="text-center p-4 bg-gray-50 rounded-lg">
            <p className="text-3xl font-bold text-gray-900">{feedback?.total || 0}</p>
            <p className="text-sm text-gray-500">Total Feedback</p>
          </div>
          <div className="text-center p-4 bg-green-50 rounded-lg">
            <p className="text-3xl font-bold text-green-600">{feedback?.reviewed || 0}</p>
            <p className="text-sm text-gray-500">Reviewed</p>
          </div>
          <div className="text-center p-4 bg-yellow-50 rounded-lg">
            <p className="text-3xl font-bold text-yellow-600">{feedback?.pending_review || 0}</p>
            <p className="text-sm text-gray-500">Pending Review</p>
          </div>
          <div className="text-center p-4 bg-blue-50 rounded-lg">
            <p className="text-3xl font-bold text-blue-600">
              {feedback?.by_type?.false_positive || 0}
            </p>
            <p className="text-sm text-gray-500">False Positives</p>
          </div>
        </div>
      </div>

      {/* Cost Budget */}
      {usage?.daily_cap_usd && (
        <div className="bg-white rounded-lg shadow p-6">
          <h2 className="text-lg font-semibold text-gray-900 mb-4">Daily Budget</h2>
          <div className="relative pt-1">
            <div className="flex mb-2 items-center justify-between">
              <div>
                <span className="text-xs font-semibold inline-block text-blue-600">
                  ${(usage?.daily_cost_usd || 0).toFixed(4)} / ${usage?.daily_cap_usd?.toFixed(2)}
                </span>
              </div>
              <div className="text-right">
                <span className="text-xs font-semibold inline-block text-blue-600">
                  {((usage?.daily_cost_usd || 0) / usage?.daily_cap_usd * 100).toFixed(1)}%
                </span>
              </div>
            </div>
            <div className="overflow-hidden h-2 text-xs flex rounded bg-blue-200">
              <div
                style={{ width: `${Math.min(100, (usage?.daily_cost_usd || 0) / usage?.daily_cap_usd * 100)}%` }}
                className="shadow-none flex flex-col text-center whitespace-nowrap text-white justify-center bg-blue-500"
              />
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

export default Overview;
