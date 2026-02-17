import React, { useState, useEffect } from 'react';
import { getMetrics } from '../services/api';
import { RefreshCw, ExternalLink } from 'lucide-react';

interface ParsedMetrics {
  analyzeRequests: number;
  detections: { category: string; action: string; count: number }[];
  totalDetections: number;
  byAction: { action: string; count: number }[];
}

const Metrics: React.FC = () => {
  const [rawMetrics, setRawMetrics] = useState('');
  const [parsed, setParsed] = useState<ParsedMetrics | null>(null);
  const [isLoading, setIsLoading] = useState(true);

  const fetchMetrics = async () => {
    setIsLoading(true);
    try {
      const data = await getMetrics();
      setRawMetrics(data);
      
      let analyzeRequests = 0;
      const detections: { category: string; action: string; count: number }[] = [];
      const actionMap: Record<string, number> = {};
      
      const lines = data.split('\n');
      lines.forEach((line: string) => {
        // Count only /analyze POST requests
        const reqMatch = line.match(/restrictor_requests_total\{endpoint="\/analyze",method="POST"[^}]*\}\s+([\d.]+)/);
        if (reqMatch && !line.includes('_created')) {
          analyzeRequests += parseFloat(reqMatch[1]);
        }
        
        // Parse detections
        const detMatch = line.match(/restrictor_detections_total\{action="([^"]+)",category="([^"]+)"\}\s+([\d.]+)/);
        if (detMatch && !line.includes('_created')) {
          const action = detMatch[1];
          const count = parseFloat(detMatch[3]);
          detections.push({ action, category: detMatch[2], count });
          actionMap[action] = (actionMap[action] || 0) + count;
        }
      });

      const byAction = Object.entries(actionMap).map(([action, count]) => ({ action, count }));

      setParsed({
        analyzeRequests,
        detections,
        totalDetections: detections.reduce((a, b) => a + b.count, 0),
        byAction,
      });
    } catch (e) {
      console.error('Failed to fetch metrics:', e);
    }
    setIsLoading(false);
  };

  useEffect(() => {
    fetchMetrics();
    const interval = setInterval(fetchMetrics, 10000);
    return () => clearInterval(interval);
  }, []);

  return (
    <div className="p-8">
      <div className="flex items-center justify-between mb-8">
        <div>
          <h1 className="text-2xl font-bold mb-1">Metrics</h1>
          <p className="text-gray-400">Real-time detection metrics</p>
        </div>
        <div className="flex items-center gap-3">
          <button onClick={fetchMetrics} disabled={isLoading} className="flex items-center gap-2 px-4 py-2 glass rounded-xl hover:bg-white/10">
            <RefreshCw className={`w-4 h-4 ${isLoading ? 'animate-spin' : ''}`} />
            Refresh
          </button>
          <a href="http://localhost:9090" target="_blank" rel="noreferrer" className="flex items-center gap-2 px-4 py-2 bg-orange-500/20 text-orange-400 rounded-xl hover:bg-orange-500/30">
            <ExternalLink className="w-4 h-4" />
            Prometheus
          </a>
          <a href="http://localhost:3001" target="_blank" rel="noreferrer" className="flex items-center gap-2 px-4 py-2 bg-yellow-500/20 text-yellow-400 rounded-xl hover:bg-yellow-500/30">
            <ExternalLink className="w-4 h-4" />
            Grafana
          </a>
        </div>
      </div>

      {parsed && (
        <div className="grid grid-cols-4 gap-6 mb-8">
          <div className="glass rounded-2xl p-6">
            <p className="text-gray-400 text-sm mb-1">Analyze Requests</p>
            <p className="text-3xl font-bold text-blue-400">{Math.round(parsed.analyzeRequests)}</p>
          </div>
          <div className="glass rounded-2xl p-6">
            <p className="text-gray-400 text-sm mb-1">Total Detections</p>
            <p className="text-3xl font-bold text-yellow-400">{Math.round(parsed.totalDetections)}</p>
          </div>
          <div className="glass rounded-2xl p-6">
            <p className="text-gray-400 text-sm mb-1">Detection Rate</p>
            <p className="text-3xl font-bold text-purple-400">
              {parsed.analyzeRequests > 0 ? `${((parsed.totalDetections / parsed.analyzeRequests) * 100).toFixed(1)}%` : '0%'}
            </p>
          </div>
          <div className="glass rounded-2xl p-6">
            <p className="text-gray-400 text-sm mb-1">Categories</p>
            <p className="text-3xl font-bold text-green-400">{parsed.detections.length}</p>
          </div>
        </div>
      )}

      <div className="grid grid-cols-2 gap-6 mb-8">
        {parsed && parsed.byAction.length > 0 && (
          <div className="glass rounded-2xl p-6">
            <h3 className="font-semibold mb-4">Actions Summary</h3>
            <div className="space-y-3">
              {parsed.byAction.map((a, i) => (
                <div key={i} className="flex items-center justify-between">
                  <div className="flex items-center gap-3">
                    <span className={`w-3 h-3 rounded-full ${a.action === 'allow' ? 'bg-green-500' : a.action === 'block' ? 'bg-red-500' : 'bg-yellow-500'}`} />
                    <span className="capitalize">{a.action}</span>
                  </div>
                  <span className="font-mono">{Math.round(a.count)}</span>
                </div>
              ))}
            </div>
          </div>
        )}
        {parsed && parsed.detections.length > 0 && (
          <div className="glass rounded-2xl p-6">
            <h3 className="font-semibold mb-4">Detections by Category</h3>
            <div className="space-y-3">
              {parsed.detections.map((d, i) => (
                <div key={i} className="flex items-center justify-between">
                  <div className="flex items-center gap-2">
                    <span className={`w-2 h-2 rounded-full ${d.action === 'block' ? 'bg-red-500' : 'bg-yellow-500'}`} />
                    <span className="text-sm">{d.category}</span>
                  </div>
                  <div className="flex items-center gap-2">
                    <span className={`text-xs px-2 py-0.5 rounded ${d.action === 'block' ? 'bg-red-500/20 text-red-400' : 'bg-yellow-500/20 text-yellow-400'}`}>{d.action}</span>
                    <span className="font-mono">{Math.round(d.count)}</span>
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}
      </div>

      <div className="glass rounded-2xl p-6">
        <h3 className="font-semibold mb-4">Raw Prometheus Metrics</h3>
        <pre className="bg-dark-800/50 rounded-xl p-4 text-sm text-gray-300 overflow-x-auto max-h-96 overflow-y-auto font-mono">{rawMetrics || 'Loading...'}</pre>
      </div>
    </div>
  );
};

export default Metrics;
