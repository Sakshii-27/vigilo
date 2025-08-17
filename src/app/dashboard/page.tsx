"use client";
import React, { useCallback, useEffect, useMemo, useState } from 'react';

type Analysis = {
  analysis_steps?: any[];
  initial_amendments?: number;
  relevant_amendments?: number;
  compliance_plan?: any;
  detailed_amendments?: any[];
};

export default function DashboardPage() {
  const API_BASE = process.env.NEXT_PUBLIC_BACKEND_URL || 'http://localhost:8000';
  const [companyId, setCompanyId] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [analysis, setAnalysis] = useState<Analysis | null>(null);
  const [progress, setProgress] = useState<string>("");

  useEffect(() => {
    try {
      const cid = localStorage.getItem('company_id');
      if (cid) setCompanyId(cid);
    } catch {}
  }, []);

  const runCompliance = useCallback(async () => {
    if (!companyId) {
      setError('No company_id found. Please submit your company details first.');
      return;
    }
    setLoading(true);
    setError(null);
    setAnalysis(null);
    setProgress('Seeding synthetic PDFs...');
    try {
      // 1) Seed local PDFs for quick testing
      await fetch(`${API_BASE}/seed/synthetic`).catch(() => {});

      // 2) Update amendments (web scrape + index)
      setProgress('Updating latest amendments...');
      await fetch(`${API_BASE}/update`).catch(() => {});

      // 3) Run compliance check for this company
      setProgress('Running prompt chain analysis...');
      const res = await fetch(`${API_BASE}/compliance/check?company_id=${encodeURIComponent(companyId)}`);
      if (!res.ok) throw new Error(`Compliance check failed: ${res.status}`);
      const json = await res.json();
      setAnalysis(json.analysis);
      setProgress('Complete');
    } catch (e: any) {
      setError(e?.message || 'Something went wrong');
    } finally {
      setLoading(false);
    }
  }, [API_BASE, companyId]);

  const header = useMemo(() => (
    <div className="flex items-center justify-between mb-8">
      <div>
        <h1 className="text-3xl font-bold text-white">Compliance Dashboard</h1>
        <p className="text-gray-400 mt-1">Monitor latest FSSAI amendments and your company's compliance status.</p>
      </div>
      <button
        onClick={runCompliance}
        disabled={loading || !companyId}
        className="bg-gradient-to-r from-emerald-500 to-cyan-500 hover:from-emerald-600 hover:to-cyan-600 disabled:opacity-50 disabled:cursor-not-allowed text-white px-6 py-3 rounded-lg font-medium transition-all duration-200"
      >
        {loading ? 'Running...' : 'Test Compliance'}
      </button>
    </div>
  ), [loading, companyId, runCompliance]);

  return (
    <div className="min-h-screen bg-gray-900 py-10">
      <div className="max-w-6xl mx-auto px-4 sm:px-6 lg:px-8">
        {header}

        {!companyId && (
          <div className="bg-yellow-500/10 border border-yellow-500/30 text-yellow-200 p-4 rounded mb-6">
            Please submit your company details from the Upload Docs page first.
          </div>
        )}

        {error && (
          <div className="bg-red-500/10 border border-red-500/30 text-red-200 p-4 rounded mb-6">
            {error}
          </div>
        )}

        {loading && (
          <div className="bg-gray-800/30 border border-gray-700/50 rounded-lg p-6 text-gray-300 mb-6">
            <div className="flex items-center">
              <div className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin mr-3"></div>
              <span>{progress}</span>
            </div>
          </div>
        )}

        {analysis && (
          <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
            <div className="lg:col-span-1 space-y-6">
              <div className="bg-gray-800/30 border border-gray-700/50 rounded-lg p-6">
                <h3 className="text-lg font-semibold text-white mb-4">Summary</h3>
                <div className="space-y-2 text-gray-300">
                  <div className="flex justify-between">
                    <span>Amendments Analyzed</span>
                    <span className="font-semibold">{analysis.initial_amendments ?? '-'}</span>
                  </div>
                  <div className="flex justify-between">
                    <span>Relevant to Company</span>
                    <span className="font-semibold">{analysis.relevant_amendments ?? '-'}</span>
                  </div>
                </div>
              </div>

              <div className="bg-gray-800/30 border border-gray-700/50 rounded-lg p-6">
                <h3 className="text-lg font-semibold text-white mb-4">Compliance Plan</h3>
                <pre className="text-xs text-gray-200 whitespace-pre-wrap bg-gray-900/40 p-4 rounded max-h-96 overflow-auto">
{JSON.stringify(analysis.compliance_plan, null, 2)}
                </pre>
              </div>
            </div>

            <div className="lg:col-span-2 bg-gray-800/30 border border-gray-700/50 rounded-lg p-6">
              <h3 className="text-lg font-semibold text-white mb-4">Relevant Amendments</h3>
              {(!analysis.detailed_amendments || analysis.detailed_amendments.length === 0) && (
                <div className="text-gray-400">No relevant amendments found.</div>
              )}
              <div className="space-y-4 max-h-[600px] overflow-auto pr-2">
                {(analysis.detailed_amendments || []).map((a: any, idx: number) => (
                  <div key={idx} className="bg-gray-900/40 border border-gray-700/50 rounded p-4">
                    <div className="flex items-start justify-between">
                      <div>
                        <div className="text-white font-medium">{a.title || `Amendment ${idx+1}`}</div>
                        <div className="text-gray-400 text-sm mt-1">{a.date || ''}</div>
                      </div>
                      <span className="text-emerald-400 text-xs px-2 py-1 rounded border border-emerald-400/40">Relevant</span>
                    </div>
                    {a.summary && (
                      <p className="text-gray-300 text-sm mt-3">{a.summary}</p>
                    )}
                    {a.actions && Array.isArray(a.actions) && a.actions.length > 0 && (
                      <div className="mt-3">
                        <div className="text-gray-200 text-sm font-medium mb-1">Suggested Actions:</div>
                        <ul className="list-disc list-inside text-gray-300 text-sm space-y-1">
                          {a.actions.map((act: string, i: number) => (
                            <li key={i}>{act}</li>
                          ))}
                        </ul>
                      </div>
                    )}
                  </div>
                ))}
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
