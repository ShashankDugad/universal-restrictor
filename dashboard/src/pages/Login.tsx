import React, { useState } from 'react';
import { useAuth } from '../contexts/AuthContext';
import { Shield, Key, ArrowRight, AlertCircle } from 'lucide-react';

const Login: React.FC = () => {
  const [apiKey, setApiKey] = useState('');
  const [error, setError] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const { login } = useAuth();

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');
    setIsLoading(true);
    
    const success = await login(apiKey);
    if (!success) {
      setError('Invalid API key. Please check and try again.');
    }
    setIsLoading(false);
  };

  const useDevKey = () => {
    setApiKey('sk-dev-1234567890abcdef12345678');
  };

  return (
    <div className="min-h-screen flex items-center justify-center p-6">
      <div className="w-full max-w-md">
        {/* Logo */}
        <div className="text-center mb-8">
          <div className="inline-flex p-4 rounded-2xl bg-gradient-to-br from-blue-500 to-purple-600 mb-4">
            <Shield className="w-12 h-12" />
          </div>
          <h1 className="text-3xl font-bold mb-2">Universal Restrictor</h1>
          <p className="text-gray-400">AI-Powered Content Moderation</p>
        </div>

        {/* Login Form */}
        <div className="glass rounded-2xl p-8">
          <h2 className="text-xl font-semibold mb-6">Sign In</h2>
          
          <form onSubmit={handleSubmit} className="space-y-4">
            <div>
              <label className="block text-sm text-gray-400 mb-2">API Key</label>
              <div className="relative">
                <Key className="absolute left-4 top-1/2 -translate-y-1/2 w-5 h-5 text-gray-500" />
                <input
                  type="password"
                  value={apiKey}
                  onChange={(e) => setApiKey(e.target.value)}
                  placeholder="sk-..."
                  className="w-full pl-12 pr-4 py-3 bg-dark-800 rounded-xl border border-white/10 focus:border-blue-500 focus:outline-none transition"
                />
              </div>
            </div>

            {error && (
              <div className="flex items-center gap-2 text-red-400 text-sm bg-red-500/10 p-3 rounded-lg">
                <AlertCircle className="w-4 h-4" />
                {error}
              </div>
            )}

            <button
              type="submit"
              disabled={!apiKey || isLoading}
              className="w-full py-3 bg-gradient-to-r from-blue-500 to-purple-600 rounded-xl font-semibold flex items-center justify-center gap-2 hover:opacity-90 disabled:opacity-50 transition"
            >
              {isLoading ? (
                <div className="w-5 h-5 border-2 border-white/30 border-t-white rounded-full animate-spin" />
              ) : (
                <>
                  Sign In
                  <ArrowRight className="w-4 h-4" />
                </>
              )}
            </button>
          </form>

          <div className="mt-6 pt-6 border-t border-white/10">
            <button
              onClick={useDevKey}
              className="w-full py-2 text-sm text-gray-400 hover:text-white transition"
            >
              Use Development Key
            </button>
          </div>
        </div>

        {/* Info */}
        <p className="text-center text-sm text-gray-500 mt-6">
          Need an API key? Contact your administrator.
        </p>
      </div>
    </div>
  );
};

export default Login;
