import React, { useState, useEffect } from 'react';
import { api } from '../api/client';

function Usage() {
  const [usage, setUsage] = useState(null);
  const [categories, setCategories] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    const fetchData = async () => {
      try {
        const [usageData, categoriesData] = await Promise.all([
          api.usage(),
          api.categories(),
        ]);
        setUsage(usageData);
        setCategories(categoriesData.categories || []);
      } catch (err) {
        setError(err.message);
      } finally {
        setLoading(false);
      }
    };

    fetchData();
    const interval = setInterval(fetchData, 30000);
    return () => clearInterval(interval);
  }, []);

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="text-gray-500">Loading usage data...</div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded">
        Error: {error}
      </div>
    );
  }

  const budgetPercentage = usage?.daily_cap_usd 
    ? ((usage?.daily_cost_usd || 0) / usage.daily_cap_usd * 100) 
    : 0;

  return (
    <div className="space-y-6">
      {/* Claude API Usage */}
      <div className="bg-white rounded-lg shadow p-6">
        <h2 className="text-lg font-semibold text-gray-900 mb-6">Claude API Usage</h2>
        
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          {/* Requests */}
          <div className="bg-gradient-to-br from-blue-50 to-blue-100 rounded-lg p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-blue-600 font-medium">Total Requests</p>
                <p className="text-3xl font-bold text-blue-900">{usage?.total_requests || 0}</p>
              </div>
              <div className="text-4xl">🤖</div>
            </div>
            <div className="mt-4 pt-4 border-t border-blue-200">
              <div className="flex justify-between text-sm">
                <span className="text-blue-600">Rate Limited</span>
                <span className="font-medium text-blue-900">{usage?.blocked_requests || 0}</span>
              </div>
            </div>
          </div>

          {/* Tokens */}
          <div className="bg-gradient-to-br from-purple-50 to-purple-100 rounded-lg p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-purple-600 font-medium">Total Tokens</p>
                <p className="text-3xl font-bold text-purple-900">
                  {((usage?.input_tokens || 0) + (usage?.output_tokens || 0)).toLocaleString()}
                </p>
              </div>
              <div className="text-4xl">📊</div>
            </div>
            <div className="mt-4 pt-4 border-t border-purple-200">
              <div className="flex justify-between text-sm mb-1">
                <span className="text-purple-600">Input</span>
                <span className="font-medium text-purple-900">{(usage?.input_tokens || 0).toLocaleString()}</span>
              </div>
              <div className="flex justify-between text-sm">
                <span className="text-purple-600">Output</span>
                <span className="font-medium text-purple-900">{(usage?.output_tokens || 0).toLocaleString()}</span>
              </div>
            </div>
          </div>

          {/* Cost */}
          <div className="bg-gradient-to-br from-green-50 to-green-100 rounded-lg p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-green-600 font-medium">Total Cost</p>
                <p className="text-3xl font-bold text-green-900">
                  ${(usage?.total_cost_usd || 0).toFixed(4)}
                </p>
              </div>
              <div className="text-4xl">💰</div>
            </div>
            <div className="mt-4 pt-4 border-t border-green-200">
              <div className="flex justify-between text-sm">
                <span className="text-green-600">Today</span>
                <span className="font-medium text-green-900">${(usage?.daily_cost_usd || 0).toFixed(4)}</span>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Daily Budget */}
      {usage?.daily_cap_usd && (
        <div className="bg-white rounded-lg shadow p-6">
          <h2 className="text-lg font-semibold text-gray-900 mb-4">Daily Budget</h2>
          
          <div className="mb-4">
            <div className="flex justify-between mb-2">
              <span className="text-sm text-gray-600">
                ${(usage?.daily_cost_usd || 0).toFixed(4)} spent of ${usage?.daily_cap_usd?.toFixed(2)} daily cap
              </span>
              <span className={`text-sm font-medium ${budgetPercentage > 80 ? 'text-red-600' : 'text-green-600'}`}>
                {budgetPercentage.toFixed(1)}% used
              </span>
            </div>
            <div className="w-full bg-gray-200 rounded-full h-4">
              <div
                className={`h-4 rounded-full transition-all ${
                  budgetPercentage > 80 ? 'bg-red-500' : budgetPercentage > 50 ? 'bg-yellow-500' : 'bg-green-500'
                }`}
                style={{ width: `${Math.min(100, budgetPercentage)}%` }}
              />
            </div>
          </div>

          <div className="bg-gray-50 rounded-lg p-4">
            <div className="flex items-center">
              <span className="text-2xl mr-3">
                {budgetPercentage > 80 ? '⚠️' : '✅'}
              </span>
              <div>
                <p className="font-medium text-gray-900">
                  {budgetPercentage > 80 
                    ? 'Approaching daily limit' 
                    : 'Budget healthy'}
                </p>
                <p className="text-sm text-gray-500">
                  Remaining: ${(usage?.remaining_daily_budget || 0).toFixed(4)}
                </p>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Pricing Info */}
      <div className="bg-white rounded-lg shadow p-6">
        <h2 className="text-lg font-semibold text-gray-900 mb-4">Claude API Pricing</h2>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div className="bg-gray-50 rounded-lg p-4">
            <p className="text-sm text-gray-500">Input Tokens</p>
            <p className="text-xl font-semibold text-gray-900">$0.25 / 1M tokens</p>
            <p className="text-xs text-gray-400 mt-1">Claude 3 Haiku</p>
          </div>
          <div className="bg-gray-50 rounded-lg p-4">
            <p className="text-sm text-gray-500">Output Tokens</p>
            <p className="text-xl font-semibold text-gray-900">$1.25 / 1M tokens</p>
            <p className="text-xs text-gray-400 mt-1">Claude 3 Haiku</p>
          </div>
        </div>
      </div>

      {/* Detection Categories */}
      <div className="bg-white rounded-lg shadow p-6">
        <h2 className="text-lg font-semibold text-gray-900 mb-4">Detection Categories</h2>
        <div className="grid grid-cols-2 md:grid-cols-4 gap-2">
          {categories.map((cat, i) => (
            <div key={i} className="bg-gray-50 px-3 py-2 rounded text-sm">
              <span className="text-gray-700">{cat.value}</span>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}

export default Usage;
