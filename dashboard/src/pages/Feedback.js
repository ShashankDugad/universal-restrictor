import React, { useState, useEffect } from 'react';
import { api } from '../api/client';

function Feedback() {
  const [feedbackList, setFeedbackList] = useState([]);
  const [stats, setStats] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    loadData();
  }, []);

  const loadData = async () => {
    try {
      const [statsData, listData] = await Promise.all([
        api.feedbackStats(),
        api.feedbackList(),
      ]);
      setStats(statsData);
      setFeedbackList(listData.feedback || []);
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  const handleReview = async (feedbackId, approved) => {
    try {
      await api.reviewFeedback(feedbackId, approved);
      loadData();
    } catch (err) {
      alert('Failed to review: ' + err.message);
    }
  };

  if (loading) return <div className="text-center py-8">Loading...</div>;

  return (
    <div className="space-y-6">
      {/* Stats */}
      <div className="grid grid-cols-4 gap-4">
        <div className="bg-white p-4 rounded-lg shadow text-center">
          <p className="text-3xl font-bold">{stats?.total || 0}</p>
          <p className="text-gray-500">Total</p>
        </div>
        <div className="bg-green-50 p-4 rounded-lg shadow text-center">
          <p className="text-3xl font-bold text-green-600">{stats?.reviewed || 0}</p>
          <p className="text-gray-500">Reviewed</p>
        </div>
        <div className="bg-yellow-50 p-4 rounded-lg shadow text-center">
          <p className="text-3xl font-bold text-yellow-600">{stats?.pending_review || 0}</p>
          <p className="text-gray-500">Pending</p>
        </div>
        <div className="bg-blue-50 p-4 rounded-lg shadow text-center">
          <p className="text-3xl font-bold text-blue-600">{stats?.by_type?.false_positive || 0}</p>
          <p className="text-gray-500">False Positives</p>
        </div>
      </div>

      {/* Feedback List */}
      <div className="bg-white rounded-lg shadow">
        <div className="p-4 border-b">
          <h2 className="text-lg font-semibold">Pending Review</h2>
        </div>
        <div className="divide-y">
          {feedbackList.filter(f => !f.reviewed).map((fb) => (
            <div key={fb.feedback_id} className="p-4">
              <div className="flex justify-between items-start">
                <div className="flex-1">
                  <div className="flex items-center space-x-2 mb-2">
                    <span className={`px-2 py-1 rounded text-xs ${
                      fb.feedback_type === 'false_positive' ? 'bg-red-100 text-red-700' :
                      fb.feedback_type === 'false_negative' ? 'bg-orange-100 text-orange-700' :
                      fb.feedback_type === 'correct' ? 'bg-green-100 text-green-700' :
                      'bg-blue-100 text-blue-700'
                    }`}>
                      {fb.feedback_type}
                    </span>
                    <span className="text-sm text-gray-500">
                      Original: {fb.original_decision}
                    </span>
                  </div>
                  <p className="text-sm text-gray-600 mb-1">
                    Categories: {fb.original_categories?.join(', ') || 'None'}
                  </p>
                  {fb.comment && (
                    <p className="text-sm bg-gray-50 p-2 rounded mt-2">
                      "{fb.comment}"
                    </p>
                  )}
                  <p className="text-xs text-gray-400 mt-2">
                    ID: {fb.feedback_id} • {new Date(fb.timestamp).toLocaleString()}
                  </p>
                </div>
                <div className="flex space-x-2 ml-4">
                  <button
                    onClick={() => handleReview(fb.feedback_id, true)}
                    className="px-3 py-1 bg-green-500 text-white rounded hover:bg-green-600"
                  >
                    ✓ Approve
                  </button>
                  <button
                    onClick={() => handleReview(fb.feedback_id, false)}
                    className="px-3 py-1 bg-red-500 text-white rounded hover:bg-red-600"
                  >
                    ✗ Reject
                  </button>
                </div>
              </div>
            </div>
          ))}
          {feedbackList.filter(f => !f.reviewed).length === 0 && (
            <div className="p-8 text-center text-gray-500">
              No pending feedback to review
            </div>
          )}
        </div>
      </div>

      {/* Reviewed List */}
      <div className="bg-white rounded-lg shadow">
        <div className="p-4 border-b">
          <h2 className="text-lg font-semibold">Reviewed</h2>
        </div>
        <div className="divide-y">
          {feedbackList.filter(f => f.reviewed).map((fb) => (
            <div key={fb.feedback_id} className="p-4 bg-gray-50">
              <div className="flex justify-between items-center">
                <div>
                  <span className={`px-2 py-1 rounded text-xs ${
                    fb.approved ? 'bg-green-100 text-green-700' : 'bg-red-100 text-red-700'
                  }`}>
                    {fb.approved ? '✓ Approved' : '✗ Rejected'}
                  </span>
                  <span className="ml-2 text-sm text-gray-600">{fb.feedback_type}</span>
                </div>
                <span className="text-xs text-gray-400">{fb.feedback_id}</span>
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}

export default Feedback;
