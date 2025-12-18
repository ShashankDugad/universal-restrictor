const API_BASE = process.env.REACT_APP_API_URL || 'http://localhost:8000';

let apiKey = localStorage.getItem('api_key') || '';

export const setApiKey = (key) => {
  apiKey = key;
  localStorage.setItem('api_key', key);
};

export const getApiKey = () => apiKey;

export const clearApiKey = () => {
  apiKey = '';
  localStorage.removeItem('api_key');
};

const fetchApi = async (endpoint, options = {}) => {
  const response = await fetch(`${API_BASE}${endpoint}`, {
    ...options,
    headers: {
      'Content-Type': 'application/json',
      'X-API-Key': apiKey,
      ...options.headers,
    },
  });
  
  if (response.status === 401 || response.status === 403) {
    throw new Error('Invalid API key');
  }
  
  if (!response.ok) {
    const error = await response.json();
    throw new Error(error.message || 'API error');
  }
  
  return response.json();
};

export const api = {
  health: () => fetch(`${API_BASE}/health`).then(r => r.json()),
  
  analyze: (text) => fetchApi('/analyze', {
    method: 'POST',
    body: JSON.stringify({ text }),
  }),
  
  usage: () => fetchApi('/usage'),
  
  categories: () => fetchApi('/categories'),
  
  feedbackStats: () => fetchApi('/feedback/stats'),
  
  feedbackList: () => fetchApi('/feedback/list'),
  
  submitFeedback: (data) => fetchApi('/feedback', {
    method: 'POST',
    body: JSON.stringify(data),
  }),
  
  reviewFeedback: (feedbackId, approved) => fetchApi(`/feedback/${feedbackId}/review`, {
    method: 'POST',
    body: JSON.stringify({ approved }),
  }),
};
