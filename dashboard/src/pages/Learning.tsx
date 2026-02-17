import React, { useState, useEffect } from 'react';
import { getLearnedPatterns, trainModel } from '../services/api';
import { Brain, Play, RefreshCw, CheckCircle, AlertTriangle, Zap } from 'lucide-react';

interface Pattern {
  pattern: string;
  category: string;
  confidence: number;
  source: string;
  created_at: string;
}

const Learning: React.FC = () => {
  const [patterns, setPatterns] = useState<Pattern[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [isTraining, setIsTraining] = useState(false);
  const [trainingResult, setTrainingResult] = useState<any>(null);

  const fetchPatterns = async () => {
    setIsLoading(true);
    try {
      const data = await getLearnedPatterns();
      setPatterns(data.patterns || []);
    } catch (e) {
      console.error('Failed to fetch patterns:', e);
    }
    setIsLoading(false);
  };

  useEffect(() => {
    fetchPatterns();
  }, []);

  const handleTrain = async () => {
    setIsTraining(true);
    setTrainingResult(null);
    try {
      const result = await trainModel();
      setTrainingResult(result);
      await fetchPatterns();
    } catch (e: any) {
      setTrainingResult({ error: e.message || 'Training failed' });
    }
    setIsTraining(false);
  };

  return (
    <div className="p-8">
      <div className="flex items-center justify-between mb-8">
        <div>
          <h1 className="text-2xl font-bold mb-1">Active Learning</h1>
          <p className="text-gray-400">Train the model from approved feedback</p>
        </div>
        <div className="flex items-center gap-3">
          <button
            onClick={fetchPatterns}
            disabled={isLoading}
            className="flex items-center gap-2 px-4 py-2 glass rounded-xl hover:bg-white/10 transition"
          >
            <RefreshCw className={`w-4 h-4 ${isLoading ? 'animate-spin' : ''}`} />
            Refresh
          </button>
          <button
            onClick={handleTrain}
            disabled={isTraining}
            className="flex items-center gap-2 px-4 py-2 bg-gradient-to-r from-purple-500 to-pink-600 rounded-xl font-semibold hover:opacity-90 disabled:opacity-50 transition"
          >
            {isTraining ? (
              <div className="w-4 h-4 border-2 border-white/30 border-t-white rounded-full animate-spin" />
            ) : (
              <Play className="w-4 h-4" />
            )}
            Train Model
          </button>
        </div>
      </div>

      {/* Training Result */}
      {trainingResult && (
        <div className={`glass rounded-xl p-4 mb-6 border ${
          trainingResult.error ? 'border-red-500/50' : 'border-green-500/50'
        }`}>
          <div className="flex items-center gap-3">
            {trainingResult.error ? (
              <AlertTriangle className="w-5 h-5 text-red-400" />
            ) : (
              <CheckCircle className="w-5 h-5 text-green-400" />
            )}
            <div>
              <p className={trainingResult.error ? 'text-red-400' : 'text-green-400'}>
                {trainingResult.error || 'Training completed successfully!'}
              </p>
              {trainingResult.patterns_learned && (
                <p className="text-sm text-gray-400">
                  {trainingResult.patterns_learned} new patterns learned
                </p>
              )}
            </div>
          </div>
        </div>
      )}

      {/* Info Cards */}
      <div className="grid grid-cols-3 gap-6 mb-8">
        <div className="glass rounded-2xl p-6">
          <div className="flex items-center gap-3 mb-4">
            <div className="p-3 rounded-xl bg-purple-500/20">
              <Brain className="w-6 h-6 text-purple-400" />
            </div>
            <div>
              <p className="text-2xl font-bold text-purple-400">{patterns.length}</p>
              <p className="text-sm text-gray-400">Learned Patterns</p>
            </div>
          </div>
        </div>

        <div className="glass rounded-2xl p-6">
          <div className="flex items-center gap-3 mb-4">
            <div className="p-3 rounded-xl bg-blue-500/20">
              <Zap className="w-6 h-6 text-blue-400" />
            </div>
            <div>
              <p className="text-2xl font-bold text-blue-400">MuRIL</p>
              <p className="text-sm text-gray-400">Base Model</p>
            </div>
          </div>
        </div>

        <div className="glass rounded-2xl p-6">
          <div className="flex items-center gap-3 mb-4">
            <div className="p-3 rounded-xl bg-green-500/20">
              <CheckCircle className="w-6 h-6 text-green-400" />
            </div>
            <div>
              <p className="text-2xl font-bold text-green-400">96.1%</p>
              <p className="text-sm text-gray-400">F1 Score</p>
            </div>
          </div>
        </div>
      </div>

      {/* How it Works */}
      <div className="glass rounded-2xl p-6 mb-8">
        <h3 className="font-semibold mb-4">How Active Learning Works</h3>
        <div className="grid grid-cols-4 gap-4">
          <div className="p-4 rounded-xl bg-dark-800/50 text-center">
            <div className="w-10 h-10 rounded-full bg-blue-500/20 flex items-center justify-center mx-auto mb-3">
              <span className="text-blue-400 font-bold">1</span>
            </div>
            <p className="text-sm font-medium">User Feedback</p>
            <p className="text-xs text-gray-400 mt-1">Users report false positives/negatives</p>
          </div>
          <div className="p-4 rounded-xl bg-dark-800/50 text-center">
            <div className="w-10 h-10 rounded-full bg-yellow-500/20 flex items-center justify-center mx-auto mb-3">
              <span className="text-yellow-400 font-bold">2</span>
            </div>
            <p className="text-sm font-medium">Review Queue</p>
            <p className="text-xs text-gray-400 mt-1">Admin approves or rejects feedback</p>
          </div>
          <div className="p-4 rounded-xl bg-dark-800/50 text-center">
            <div className="w-10 h-10 rounded-full bg-purple-500/20 flex items-center justify-center mx-auto mb-3">
              <span className="text-purple-400 font-bold">3</span>
            </div>
            <p className="text-sm font-medium">Pattern Extraction</p>
            <p className="text-xs text-gray-400 mt-1">System learns new detection patterns</p>
          </div>
          <div className="p-4 rounded-xl bg-dark-800/50 text-center">
            <div className="w-10 h-10 rounded-full bg-green-500/20 flex items-center justify-center mx-auto mb-3">
              <span className="text-green-400 font-bold">4</span>
            </div>
            <p className="text-sm font-medium">Model Update</p>
            <p className="text-xs text-gray-400 mt-1">Patterns added to detection pipeline</p>
          </div>
        </div>
      </div>

      {/* Learned Patterns Table */}
      <div className="glass rounded-2xl overflow-hidden">
        <div className="p-4 border-b border-white/10">
          <h3 className="font-semibold">Learned Patterns</h3>
        </div>
        {isLoading ? (
          <div className="p-8 text-center">
            <div className="w-8 h-8 border-2 border-purple-500/30 border-t-purple-500 rounded-full animate-spin mx-auto mb-4" />
            <p className="text-gray-400">Loading patterns...</p>
          </div>
        ) : patterns.length === 0 ? (
          <div className="p-8 text-center text-gray-400">
            <Brain className="w-12 h-12 mx-auto mb-4 opacity-50" />
            <p>No learned patterns yet</p>
            <p className="text-sm mt-2">Approve feedback to generate new patterns</p>
          </div>
        ) : (
          <table className="w-full">
            <thead className="bg-dark-800/50">
              <tr>
                <th className="text-left p-4 text-sm text-gray-400 font-medium">Pattern</th>
                <th className="text-left p-4 text-sm text-gray-400 font-medium">Category</th>
                <th className="text-left p-4 text-sm text-gray-400 font-medium">Confidence</th>
                <th className="text-left p-4 text-sm text-gray-400 font-medium">Source</th>
                <th className="text-left p-4 text-sm text-gray-400 font-medium">Created</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-white/10">
              {patterns.map((pattern, i) => (
                <tr key={i} className="hover:bg-white/5">
                  <td className="p-4 font-mono text-sm">{pattern.pattern}</td>
                  <td className="p-4">
                    <span className="px-2 py-1 rounded bg-blue-500/20 text-blue-400 text-xs">
                      {pattern.category}
                    </span>
                  </td>
                  <td className="p-4">
                    <span className={`${
                      pattern.confidence > 0.9 ? 'text-green-400' :
                      pattern.confidence > 0.7 ? 'text-yellow-400' : 'text-red-400'
                    }`}>
                      {(pattern.confidence * 100).toFixed(0)}%
                    </span>
                  </td>
                  <td className="p-4 text-sm text-gray-400">{pattern.source}</td>
                  <td className="p-4 text-sm text-gray-400">
                    {new Date(pattern.created_at).toLocaleDateString()}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>
    </div>
  );
};

export default Learning;
