import axios from 'axios';

const API_URL = 'http://localhost:8000';

const api = axios.create({
  baseURL: API_URL,
  headers: { 'Content-Type': 'application/json' },
});

api.interceptors.request.use((config) => {
  const apiKey = localStorage.getItem('apiKey') || 'sk-dev-1234567890abcdef12345678';
  config.headers['X-API-Key'] = apiKey;
  return config;
});

export interface Detection {
  category: string;
  severity: string;
  confidence: number;
  detector: string;
  explanation: string;
  matched_text?: string;
}

export interface AnalyzeResponse {
  action: 'allow' | 'block' | 'redact' | 'warn';
  detections: Detection[];
  redacted_text: string | null;
  request_id: string;
  processing_time_ms: number;
  summary: {
    categories_found: string[];
    max_severity: string | null;
    max_confidence: number;
    detection_count: number;
  };
}

export interface FeedbackItem {
  feedback_id: string;
  tenant_id: string;
  request_id: string;
  input_hash: string;
  input_length: number;
  original_decision: string;
  original_categories: string[];
  original_confidence: number;
  feedback_type: string;
  corrected_category?: string;
  comment?: string;
  timestamp: string;
  reviewed: boolean;
  approved?: boolean;
  reviewed_at?: string;
  reviewed_by?: string;
  included_in_training: boolean;
}

export interface FeedbackStats {
  total: number;
  by_type: Record<string, number>;
  reviewed: number;
  pending_review: number;
}

export interface HealthResponse {
  status: string;
  version: string;
  timestamp: string;
}

export const analyzeText = async (text: string): Promise<AnalyzeResponse> => {
  const response = await api.post('/analyze', { text });
  return response.data;
};

export const getHealth = async (): Promise<HealthResponse> => {
  const response = await api.get('/health');
  return response.data;
};

export const getFeedbackList = async (): Promise<{ feedback: FeedbackItem[] }> => {
  const response = await api.get('/feedback/list');
  return response.data;
};

export const getFeedbackStats = async (): Promise<FeedbackStats> => {
  const response = await api.get('/feedback/stats');
  return response.data;
};

export const reviewFeedback = async (feedbackId: string, approved: boolean): Promise<any> => {
  const response = await api.post(`/feedback/${feedbackId}/review`, { approved });
  return response.data;
};

export const submitFeedback = async (data: { request_id: string; feedback_type: string; comment?: string }): Promise<any> => {
  const response = await api.post('/feedback', data);
  return response.data;
};

export const getMetrics = async (): Promise<string> => {
  const response = await api.get('/metrics');
  return response.data;
};

export const getLearnedPatterns = async (): Promise<any> => {
  try {
    const response = await api.get('/admin/learned-patterns');
    return response.data;
  } catch {
    return { patterns: [] };
  }
};

export const trainModel = async (): Promise<any> => {
  const response = await api.post('/admin/train');
  return response.data;
};

export const getClaudeUsage = async (): Promise<any> => {
  try {
    const response = await api.get('/admin/claude-usage');
    return response.data;
  } catch {
    return { total_calls: 0, total_tokens: 0, estimated_cost: 0 };
  }
};

export default api;

export interface UsageResponse {
  total_requests: number;
  blocked_requests: number;
  input_tokens: number;
  output_tokens: number;
  total_tokens: number;
  total_cost_usd: number;
  daily_cost_usd: number;
  daily_cap_usd: number;
  remaining_daily_budget: number;
  requests_per_minute_limit: number;
}

export const getUsage = async (): Promise<UsageResponse> => {
  const response = await api.get('/usage');
  return response.data;
};
