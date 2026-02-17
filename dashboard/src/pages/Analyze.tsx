import React, { useState } from 'react';
import { analyzeText, type AnalyzeResponse } from '../services/api';
import { Send, CheckCircle, XCircle, AlertTriangle, Clock, Zap } from 'lucide-react';

const Analyze: React.FC = () => {
  const [text, setText] = useState('');
  const [result, setResult] = useState<AnalyzeResponse | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [history, setHistory] = useState<Array<AnalyzeResponse & { text: string; time: string }>>([]);

  const samples = [
    { label: '✅ Safe', text: 'Hello, how are you today?', color: 'green' },
    { label: '🇮🇳 Hindi Safe', text: 'namaste kaise ho', color: 'green' },
    { label: '🔴 Hindi Slur', text: 'bhenchod', color: 'red' },
    { label: '🔴 Threat', text: 'I will kill you', color: 'red' },
    { label: '🔴 Harassment', text: 'you are worthless garbage', color: 'red' },
    { label: '🟡 PII Email', text: 'My email is test@example.com', color: 'yellow' },
    { label: '🔴 Dangerous', text: 'how to make a bomb', color: 'red' },
    { label: '🔴 Self-harm', text: 'I want to kill myself', color: 'red' },
  ];

  const handleAnalyze = async (inputText: string = text) => {
    if (!inputText.trim()) return;
    setIsLoading(true);
    try {
      const response = await analyzeText(inputText);
      setResult(response);
      setHistory(prev => [{
        ...response,
        text: inputText,
        time: new Date().toLocaleTimeString()
      }, ...prev.slice(0, 19)]);
    } catch (e) {
      console.error('Analysis failed:', e);
    }
    setIsLoading(false);
  };

  const actionConfig = {
    allow: { icon: CheckCircle, color: 'green', bg: 'bg-green-500/20', border: 'border-green-500/50', text: 'text-green-400' },
    block: { icon: XCircle, color: 'red', bg: 'bg-red-500/20', border: 'border-red-500/50', text: 'text-red-400' },
    redact: { icon: AlertTriangle, color: 'yellow', bg: 'bg-yellow-500/20', border: 'border-yellow-500/50', text: 'text-yellow-400' },
    warn: { icon: AlertTriangle, color: 'orange', bg: 'bg-orange-500/20', border: 'border-orange-500/50', text: 'text-orange-400' },
  };

  return (
    <div className="p-8">
      <div className="mb-8">
        <h1 className="text-2xl font-bold mb-1">Analyze Content</h1>
        <p className="text-gray-400">Test the content moderation pipeline in real-time</p>
      </div>

      <div className="grid grid-cols-3 gap-6">
        {/* Input Section */}
        <div className="col-span-2 space-y-6">
          <div className="glass rounded-2xl p-6">
            <div className="flex items-center justify-between mb-4">
              <h3 className="font-semibold">Input Text</h3>
              <span className="text-xs text-gray-500">⌘ + Enter to analyze</span>
            </div>
            <textarea
              value={text}
              onChange={(e) => setText(e.target.value)}
              onKeyDown={(e) => e.key === 'Enter' && e.metaKey && handleAnalyze()}
              placeholder="Enter text to analyze for toxicity, hate speech, PII, etc..."
              className="w-full h-40 bg-dark-800/50 rounded-xl p-4 text-white placeholder-gray-500 focus:outline-none focus:ring-2 focus:ring-blue-500/50 resize-none"
            />
            
            {/* Sample buttons */}
            <div className="flex flex-wrap gap-2 mt-4">
              {samples.map((sample, i) => (
                <button
                  key={i}
                  onClick={() => { setText(sample.text); handleAnalyze(sample.text); }}
                  className={`px-3 py-1.5 text-xs rounded-lg bg-dark-600 hover:bg-dark-500 transition border border-${sample.color}-500/30`}
                >
                  {sample.label}
                </button>
              ))}
            </div>

            <div className="flex justify-end mt-4">
              <button
                onClick={() => handleAnalyze()}
                disabled={isLoading || !text.trim()}
                className="px-6 py-3 bg-gradient-to-r from-blue-500 to-purple-600 rounded-xl font-semibold flex items-center gap-2 hover:opacity-90 disabled:opacity-50 transition"
              >
                {isLoading ? (
                  <div className="w-5 h-5 border-2 border-white/30 border-t-white rounded-full animate-spin" />
                ) : (
                  <>
                    <Send className="w-4 h-4" />
                    Analyze
                  </>
                )}
              </button>
            </div>
          </div>

          {/* Result */}
          {result && (
            <div className={`glass rounded-2xl p-6 border ${actionConfig[result.action]?.border}`}>
              <div className="flex items-center justify-between mb-6">
                <div className="flex items-center gap-3">
                  {React.createElement(actionConfig[result.action]?.icon || AlertTriangle, {
                    className: `w-8 h-8 ${actionConfig[result.action]?.text}`
                  })}
                  <div>
                    <span className={`text-3xl font-bold uppercase ${actionConfig[result.action]?.text}`}>
                      {result.action}
                    </span>
                    <div className="flex items-center gap-2 text-xs text-gray-500 mt-1">
                      <Clock className="w-3 h-3" />
                      {result.processing_time_ms}ms
                      <span className="text-gray-600">•</span>
                      <span className="font-mono">{result.request_id?.slice(0, 8)}</span>
                    </div>
                  </div>
                </div>
              </div>

              {result.detections && result.detections.length > 0 && (
                <div className="space-y-3">
                  <h4 className="text-sm font-semibold text-gray-300 uppercase tracking-wider">Detections ({result.detections.length})</h4>
                  {result.detections.map((d, i) => (
                    <div key={i} className="bg-dark-800/50 rounded-xl p-4">
                      <div className="flex items-center justify-between mb-2">
                        <span className="font-semibold text-white">{d.category}</span>
                        <div className="flex items-center gap-2">
                          <span className={`px-2 py-1 rounded-full text-xs ${
                            d.confidence > 0.9 ? 'bg-red-500/20 text-red-400' :
                            d.confidence > 0.7 ? 'bg-yellow-500/20 text-yellow-400' :
                            'bg-blue-500/20 text-blue-400'
                          }`}>
                            {(d.confidence * 100).toFixed(0)}%
                          </span>
                        </div>
                      </div>
                      <div className="flex items-center gap-2 text-xs mb-2">
                        <span className="px-2 py-0.5 rounded bg-dark-600 text-gray-400">{d.detector}</span>
                        <span className="px-2 py-0.5 rounded bg-dark-600 text-gray-400">{d.severity}</span>
                      </div>
                      <p className="text-sm text-gray-400">{d.explanation}</p>
                    </div>
                  ))}
                </div>
              )}

              {result.redacted_text && (
                <div className="mt-4 p-4 bg-dark-800/50 rounded-xl">
                  <h4 className="text-sm font-semibold text-gray-300 mb-2">Redacted Output</h4>
                  <p className="font-mono text-yellow-400">{result.redacted_text}</p>
                </div>
              )}

              {result.action === 'allow' && result.detections?.length === 0 && (
                <div className="text-center py-4 text-gray-400">
                  <CheckCircle className="w-12 h-12 mx-auto mb-2 text-green-400" />
                  <p>Content is safe - no issues detected</p>
                </div>
              )}
            </div>
          )}
        </div>

        {/* History Sidebar */}
        <div className="glass rounded-2xl p-6 h-fit max-h-[calc(100vh-200px)] overflow-hidden flex flex-col">
          <h3 className="font-semibold mb-4">History ({history.length})</h3>
          <div className="flex-1 overflow-y-auto space-y-2">
            {history.length === 0 ? (
              <p className="text-gray-500 text-sm text-center py-8">No history yet</p>
            ) : (
              history.map((item, i) => (
                <div
                  key={i}
                  onClick={() => { setText(item.text); setResult(item); }}
                  className={`p-3 rounded-lg border cursor-pointer hover:bg-white/5 transition ${actionConfig[item.action]?.border}`}
                >
                  <div className="flex items-center justify-between mb-1">
                    <span className={`text-xs font-bold uppercase ${actionConfig[item.action]?.text}`}>
                      {item.action}
                    </span>
                    <span className="text-xs text-gray-500">{item.time}</span>
                  </div>
                  <p className="text-sm text-gray-300 truncate">{item.text}</p>
                  <div className="flex gap-1 mt-1 flex-wrap">
                    {item.detections?.slice(0, 2).map((d, j) => (
                      <span key={j} className="text-xs px-1.5 py-0.5 rounded bg-dark-600 text-gray-400">
                        {d.detector?.split('_').pop()}
                      </span>
                    ))}
                  </div>
                </div>
              ))
            )}
          </div>
        </div>
      </div>
    </div>
  );
};

export default Analyze;
