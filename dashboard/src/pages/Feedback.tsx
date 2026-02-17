import React, { useState, useEffect } from 'react';
import { getFeedbackList, getFeedbackStats, reviewFeedback, type FeedbackItem, type FeedbackStats } from '../services/api';
import { CheckCircle, XCircle, Clock, Filter, RefreshCw, ThumbsUp, ThumbsDown } from 'lucide-react';

const Feedback: React.FC = () => {
  const [feedback, setFeedback] = useState<FeedbackItem[]>([]);
  const [stats, setStats] = useState<FeedbackStats | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [filter, setFilter] = useState<'all' | 'pending' | 'reviewed'>('all');
  const [processing, setProcessing] = useState<string | null>(null);

  const fetchData = async () => {
    setIsLoading(true);
    try {
      const [feedbackRes, statsRes] = await Promise.all([
        getFeedbackList(),
        getFeedbackStats()
      ]);
      setFeedback(feedbackRes.feedback || []);
      setStats(statsRes);
    } catch (e) {
      console.error('Failed to fetch feedback:', e);
    }
    setIsLoading(false);
  };

  useEffect(() => {
    fetchData();
  }, []);

  const handleReview = async (feedbackId: string, approved: boolean) => {
    setProcessing(feedbackId);
    try {
      await reviewFeedback(feedbackId, approved);
      await fetchData();
    } catch (e) {
      console.error('Review failed:', e);
    }
    setProcessing(null);
  };

  const filteredFeedback = feedback.filter(f => {
    if (filter === 'pending') return !f.reviewed;
    if (filter === 'reviewed') return f.reviewed;
    return true;
  });

  const typeColors: Record<string, string> = {
    correct: 'bg-green-500/20 text-green-400 border-green-500/30',
    false_positive: 'bg-red-500/20 text-red-400 border-red-500/30',
    false_negative: 'bg-yellow-500/20 text-yellow-400 border-yellow-500/30',
  };

  return (
    <div className="p-8">
      <div className="flex items-center justify-between mb-8">
        <div>
          <h1 className="text-2xl font-bold mb-1">Feedback Management</h1>
          <p className="text-gray-400">Review and approve user feedback for model training</p>
        </div>
        <button
          onClick={fetchData}
          disabled={isLoading}
          className="flex items-center gap-2 px-4 py-2 glass rounded-xl hover:bg-white/10 transition"
        >
          <RefreshCw className={`w-4 h-4 ${isLoading ? 'animate-spin' : ''}`} />
          Refresh
        </button>
      </div>

      {/* Stats */}
      {stats && (
        <div className="grid grid-cols-5 gap-4 mb-8">
          <div className="glass rounded-xl p-4 text-center">
            <p className="text-2xl font-bold text-white">{stats.total}</p>
            <p className="text-xs text-gray-400">Total Feedback</p>
          </div>
          <div className="glass rounded-xl p-4 text-center">
            <p className="text-2xl font-bold text-green-400">{stats.by_type?.correct || 0}</p>
            <p className="text-xs text-gray-400">Correct</p>
          </div>
          <div className="glass rounded-xl p-4 text-center">
            <p className="text-2xl font-bold text-red-400">{stats.by_type?.false_positive || 0}</p>
            <p className="text-xs text-gray-400">False Positive</p>
          </div>
          <div className="glass rounded-xl p-4 text-center">
            <p className="text-2xl font-bold text-yellow-400">{stats.by_type?.false_negative || 0}</p>
            <p className="text-xs text-gray-400">False Negative</p>
          </div>
          <div className="glass rounded-xl p-4 text-center border border-orange-500/30">
            <p className="text-2xl font-bold text-orange-400">{stats.pending_review}</p>
            <p className="text-xs text-gray-400">Pending Review</p>
          </div>
        </div>
      )}

      {/* Filter */}
      <div className="flex items-center gap-2 mb-6">
        <Filter className="w-4 h-4 text-gray-400" />
        <span className="text-sm text-gray-400 mr-2">Filter:</span>
        {(['all', 'pending', 'reviewed'] as const).map(f => (
          <button
            key={f}
            onClick={() => setFilter(f)}
            className={`px-3 py-1.5 text-sm rounded-lg transition ${
              filter === f
                ? 'bg-blue-500/20 text-blue-400 border border-blue-500/30'
                : 'bg-dark-600 text-gray-400 hover:bg-dark-500'
            }`}
          >
            {f.charAt(0).toUpperCase() + f.slice(1)}
            {f === 'pending' && stats?.pending_review ? ` (${stats.pending_review})` : ''}
          </button>
        ))}
      </div>

      {/* Feedback List */}
      <div className="glass rounded-2xl overflow-hidden">
        {isLoading ? (
          <div className="p-8 text-center">
            <div className="w-8 h-8 border-2 border-blue-500/30 border-t-blue-500 rounded-full animate-spin mx-auto mb-4" />
            <p className="text-gray-400">Loading feedback...</p>
          </div>
        ) : filteredFeedback.length === 0 ? (
          <div className="p-8 text-center text-gray-400">
            <Clock className="w-12 h-12 mx-auto mb-4 opacity-50" />
            <p>No feedback found</p>
          </div>
        ) : (
          <div className="divide-y divide-white/10">
            {filteredFeedback.map((item) => (
              <div key={item.feedback_id} className="p-4 hover:bg-white/5 transition">
                <div className="flex items-start justify-between gap-4">
                  <div className="flex-1">
                    <div className="flex items-center gap-2 mb-2">
                      <span className={`px-2 py-1 text-xs rounded-lg border ${typeColors[item.feedback_type] || 'bg-gray-500/20 text-gray-400'}`}>
                        {item.feedback_type?.replace('_', ' ')}
                      </span>
                      <span className="text-xs text-gray-500">
                        {new Date(item.timestamp).toLocaleString()}
                      </span>
                      {item.reviewed && (
                        <span className={`flex items-center gap-1 text-xs ${item.approved ? 'text-green-400' : 'text-red-400'}`}>
                          {item.approved ? <CheckCircle className="w-3 h-3" /> : <XCircle className="w-3 h-3" />}
                          {item.approved ? 'Approved' : 'Rejected'}
                        </span>
                      )}
                      {item.included_in_training && (
                        <span className="text-xs text-purple-400">✓ Trained</span>
                      )}
                    </div>
                    <div className="grid grid-cols-2 gap-4 text-sm">
                      <div>
                        <p className="text-gray-500 text-xs mb-1">Original Decision</p>
                        <p className="text-white">{item.original_decision}</p>
                      </div>
                      <div>
                        <p className="text-gray-500 text-xs mb-1">Categories</p>
                        <p className="text-white">{item.original_categories?.join(', ') || 'None'}</p>
                      </div>
                    </div>
                    {item.comment && (
                      <div className="mt-2 p-2 rounded bg-dark-800/50 text-sm text-gray-300">
                        "{item.comment}"
                      </div>
                    )}
                    <div className="flex items-center gap-4 mt-2 text-xs text-gray-500">
                      <span>ID: {item.feedback_id}</span>
                      <span>Length: {item.input_length} chars</span>
                      <span>Confidence: {(item.original_confidence * 100).toFixed(0)}%</span>
                    </div>
                  </div>

                  {/* Actions */}
                  {!item.reviewed && (
                    <div className="flex items-center gap-2">
                      <button
                        onClick={() => handleReview(item.feedback_id, true)}
                        disabled={processing === item.feedback_id}
                        className="flex items-center gap-1 px-3 py-2 bg-green-500/20 text-green-400 rounded-lg hover:bg-green-500/30 transition disabled:opacity-50"
                      >
                        {processing === item.feedback_id ? (
                          <div className="w-4 h-4 border-2 border-green-400/30 border-t-green-400 rounded-full animate-spin" />
                        ) : (
                          <ThumbsUp className="w-4 h-4" />
                        )}
                        Approve
                      </button>
                      <button
                        onClick={() => handleReview(item.feedback_id, false)}
                        disabled={processing === item.feedback_id}
                        className="flex items-center gap-1 px-3 py-2 bg-red-500/20 text-red-400 rounded-lg hover:bg-red-500/30 transition disabled:opacity-50"
                      >
                        {processing === item.feedback_id ? (
                          <div className="w-4 h-4 border-2 border-red-400/30 border-t-red-400 rounded-full animate-spin" />
                        ) : (
                          <ThumbsDown className="w-4 h-4" />
                        )}
                        Reject
                      </button>
                    </div>
                  )}
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
};

export default Feedback;
