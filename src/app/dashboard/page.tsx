"use client";
import React, { useCallback, useEffect, useMemo, useState } from 'react';
import { TestTube, Bell, Settings, Calendar, FileText, ChevronRight } from 'lucide-react';

type CompliancePlan = {
  timeline?: { timeframe: string; actions: { department: string; task: string; steps?: string[]; urgency?: string; amendments?: string[] }[] }[];
  summary?: { critical_items?: number; high_priority?: number; total_actions?: number };
  status?: string;
  notes?: string;
  next_steps?: string[];
};

type Analysis = {
  analysis_steps?: Record<string, string[]>;
  initial_amendments?: number;
  relevant_amendments?: number;
  compliance_plan?: CompliancePlan;
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
      await fetch(`${API_BASE}/seed/synthetic`).catch(() => {});
      setProgress('Updating latest amendments...');
      await fetch(`${API_BASE}/update`).catch(() => {});
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
        <h1 className="text-2xl font-semibold text-white mb-1">Compliance Hub</h1>
        <p className="text-gray-400">Regulatory Intelligence</p>
      </div>
      <div className="flex items-center gap-3">
        <button onClick={runCompliance} disabled={loading || !companyId} className="bg-emerald-600 hover:bg-emerald-700 disabled:opacity-50 text-white px-4 py-2.5 rounded-lg font-medium transition-colors flex items-center gap-2">
          <TestTube className="h-4 w-4" /> {loading ? 'Running...' : 'Test Compliance'}
        </button>
        <button className="p-2 text-gray-400 hover:text-white hover:bg-gray-800 rounded-lg transition-colors">
          <Bell className="h-5 w-5" />
        </button>
        <button className="p-2 text-gray-400 hover:text-white hover:bg-gray-800 rounded-lg transition-colors">
          <Settings className="h-5 w-5" />
        </button>
      </div>
    </div>
  ), [loading, companyId, runCompliance]);

  const Plan = ({ plan }: { plan?: CompliancePlan }) => {
    if (!plan) return null;
    const tl = plan.timeline || [];
    return (
      <div className="space-y-4">
        {tl.map((slot, idx) => (
          <div key={idx} className="bg-black border border-gray-800 rounded-lg p-4">
            <div className="text-white font-medium mb-2">{slot.timeframe}</div>
            <div className="space-y-3">
              {(slot.actions || []).map((a, i) => (
                <div key={i} className="bg-gray-900 border border-gray-800 rounded p-3">
                  <div className="flex items-center justify-between">
                    <div className="text-gray-200 text-sm font-medium">{a.department}</div>
                    {a.urgency && (
                      <span className={`px-2 py-0.5 rounded text-xs ${a.urgency === 'Critical' ? 'bg-red-900/40 text-red-400' : a.urgency === 'High' ? 'bg-yellow-900/30 text-yellow-400' : 'bg-emerald-900/30 text-emerald-400'}`}>{a.urgency}</span>
                    )}
                  </div>
                  <div className="text-white text-sm mt-1">{a.task}</div>
                  {a.amendments && a.amendments.length > 0 && (
                    <div className="text-xs text-gray-400 mt-1">Refs: {a.amendments.join(', ')}</div>
                  )}
                  {a.steps && a.steps.length > 0 && (
                    <ul className="list-disc list-inside text-gray-300 text-sm mt-2 space-y-1">
                      {a.steps.map((s, k) => (<li key={k}>{s}</li>))}
                    </ul>
                  )}
                </div>
              ))}
            </div>
          </div>
        ))}
        {plan.summary && (
          <div className="text-gray-300 text-sm">Summary: {plan.summary.total_actions ?? 0} actions • High: {plan.summary.high_priority ?? 0} • Critical: {plan.summary.critical_items ?? 0}</div>
        )}
        {plan.status && (
          <div className="text-xs text-gray-400">Status: {plan.status} {plan.notes ? `• ${plan.notes}` : ''}</div>
        )}
        {plan.next_steps && plan.next_steps.length > 0 && (
          <div className="text-xs text-gray-400">Next: {plan.next_steps.join('; ')}</div>
        )}
      </div>
    );
  };

  const Amendments = ({ items }: { items: any[] }) => (
    <div className="space-y-4">
      {items.map((a, idx) => (
        <div key={idx} className="bg-gray-900 border border-gray-800 rounded-lg p-4">
          <div className="flex items-start justify-between mb-1">
            <div>
              <div className="text-white font-medium">{a.title || `Amendment ${idx + 1}`}</div>
              <div className="text-gray-400 text-xs mt-1 flex items-center gap-2"><Calendar className="h-3 w-3" /> {a.date || ''}</div>
            </div>
            <span className="px-2 py-0.5 rounded text-xs bg-emerald-900/30 text-emerald-400 border border-emerald-800">Relevant</span>
          </div>
          {a.summary && <p className="text-gray-300 text-sm mt-2">{a.summary}</p>}
          {Array.isArray(a.requirements) && a.requirements.length > 0 && (
            <div className="mt-2">
              <div className="text-gray-200 text-sm font-medium mb-1">Key Requirements</div>
              <ul className="list-disc list-inside text-gray-300 text-sm space-y-1">
                {a.requirements.map((r: string, i: number) => (<li key={i}>{r}</li>))}
              </ul>
            </div>
          )}
          {a.relevance_reason && (
            <div className="text-gray-400 text-xs mt-2">Reason: {a.relevance_reason}</div>
          )}
          {Array.isArray(a.product_impacts) && a.product_impacts.length > 0 && (
            <div className="mt-3">
              <div className="text-gray-200 text-sm font-medium mb-1">Product Impacts</div>
              <div className="space-y-2">
                {a.product_impacts.map((pi: any, i: number) => (
                  <div key={i} className="bg-black border border-gray-800 rounded p-3">
                    <div className="text-white text-sm">{pi.product_name}</div>
                    {Array.isArray(pi.affected_aspects) && pi.affected_aspects.length > 0 && (
                      <div className="text-xs text-gray-400 mt-1">Affected: {pi.affected_aspects.join(', ')}</div>
                    )}
                    {Array.isArray(pi.required_changes) && pi.required_changes.length > 0 && (
                      <ul className="list-disc list-inside text-gray-300 text-sm mt-1 space-y-1">
                        {pi.required_changes.map((s: string, k: number) => (<li key={k}>{s}</li>))}
                      </ul>
                    )}
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      ))}
    </div>
  );

  return (
    <div className="min-h-screen bg-black">
      <div className="flex">
        {/* Left Sidebar */}
        <div className="w-72 bg-gray-900 border-r border-gray-800 p-6 relative">
          {header}
          {/* Bottom Stats */}
          <div className="absolute bottom-6 left-6 right-6">
            <div className="border-t border-gray-800 pt-4">
              <div className="text-gray-400 text-xs mb-2">Compliance Status</div>
              <div className="flex items-center justify-between text-sm">
                <span className="text-white">Overall Score</span>
                <span className="text-emerald-400 font-semibold">{analysis?.compliance_plan?.summary?.total_actions ? Math.min(100, 60 + (analysis.compliance_plan.summary.total_actions || 0) * 5) : 80}%</span>
              </div>
            </div>
          </div>
        </div>

        {/* Main Content */}
        <div className="flex-1 flex">
          {/* Compliance View */}
          <div className="flex-1 p-8">
            {/* Progress / Errors */}
            {(!companyId) && (
              <div className="bg-yellow-500/10 border border-yellow-500/30 text-yellow-200 p-4 rounded mb-6">
                Please submit your company details from the Upload Docs page first.
              </div>
            )}
            {error && (
              <div className="bg-red-500/10 border border-red-500/30 text-red-200 p-4 rounded mb-6">{error}</div>
            )}
            {loading && (
              <div className="bg-gray-900 border border-gray-800 rounded-lg p-4 text-gray-300 mb-6 flex items-center gap-3">
                <div className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin"></div>
                <span>{progress}</span>
              </div>
            )}

            {analysis ? (
              <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
                <div className="lg:col-span-1">
                  <div className="bg-gray-900 border border-gray-800 rounded-lg p-6 mb-6">
                    <div className="text-white font-medium mb-2">Summary</div>
                    <div className="text-sm text-gray-300 space-y-2">
                      <div className="flex items-center justify-between"><span>Amendments Analyzed</span><span className="font-semibold">{analysis.initial_amendments ?? '-'}</span></div>
                      <div className="flex items-center justify-between"><span>Relevant</span><span className="font-semibold">{analysis.relevant_amendments ?? '-'}</span></div>
                    </div>
                  </div>
                  <div className="bg-gray-900 border border-gray-800 rounded-lg p-6">
                    <div className="text-white font-medium mb-3">Compliance Plan</div>
                    <Plan plan={analysis.compliance_plan} />
                  </div>
                </div>
                <div className="lg:col-span-2">
                  <div className="bg-gray-900 border border-gray-800 rounded-lg p-6">
                    <div className="flex items-center justify-between mb-4">
                      <div className="text-white font-medium">Relevant Amendments</div>
                      <div className="text-xs text-gray-400">Latest insights</div>
                    </div>
                    {(!analysis.detailed_amendments || analysis.detailed_amendments.length === 0) ? (
                      <div className="text-gray-400">No relevant amendments found.</div>
                    ) : (
                      <Amendments items={analysis.detailed_amendments!} />
                    )}
                  </div>
                </div>
              </div>
            ) : (
              <div className="text-gray-400">Click "Test Compliance" to run the analysis.</div>
            )}
          </div>

          {/* Right Sidebar - Stage Logs */}
          <div className="w-80 bg-gray-900 border-l border-gray-800 p-6">
            <h3 className="text-white font-medium text-lg mb-4">Process Logs</h3>
            <div className="space-y-3 max-h-[80vh] overflow-auto pr-1">
              {analysis && Object.entries(analysis.analysis_steps || {}).map(([stage, logs]) => (
                <div key={stage} className="bg-black border border-gray-800 rounded p-3">
                  <div className="text-gray-200 text-sm font-medium mb-1">{stage}</div>
                  <ul className="text-xs text-gray-400 space-y-1">
                    {(logs as string[]).map((l, i) => (<li key={i} className="flex items-start gap-2"><ChevronRight className="h-3 w-3 mt-0.5" /> <span>{l}</span></li>))}
                  </ul>
                </div>
              ))}
              {!analysis && (
                <div className="text-gray-500 text-sm">No logs yet.</div>
              )}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
