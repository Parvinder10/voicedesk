import React, { useState, useEffect } from 'react';
import { api } from '../services/api';
import { BarChart3, TrendingUp, PhoneCall, Calendar, Headphones, Clock, CheckCircle2, Award } from 'lucide-react';

export const AnalyticsPage: React.FC = () => {
  const [data, setData] = useState<any>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    api.getDashboardOverview()
      .then(setData)
      .catch(console.error)
      .finally(() => setLoading(false));
  }, []);

  if (loading) {
    return <div className="p-8 text-center text-xs text-slate-400">Loading analytics intelligence...</div>;
  }

  const metrics = data?.metrics || {};
  const outcomes = data?.outcomes_breakdown || {};
  const peakHours = data?.peak_calling_hours || [];

  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-xl font-bold text-white tracking-tight">Receptionist Analytics & Performance</h2>
        <p className="text-xs text-slate-400 mt-0.5">
          Real-time aggregated metrics computed from actual persisted call sessions and appointment records.
        </p>
      </div>

      {/* KPI Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        <div className="p-5 rounded-2xl bg-slate-900 border border-slate-800">
          <div className="text-xs text-slate-400 uppercase font-semibold">Total Inbound Calls</div>
          <div className="text-3xl font-extrabold text-white mt-1">{metrics.total_calls || 0}</div>
          <div className="text-xs text-emerald-400 mt-1">{metrics.answered_calls || 0} answered ({metrics.resolution_rate_percentage || 100}%)</div>
        </div>

        <div className="p-5 rounded-2xl bg-slate-900 border border-slate-800">
          <div className="text-xs text-slate-400 uppercase font-semibold">Total Bookings</div>
          <div className="text-3xl font-extrabold text-white mt-1">{metrics.total_appointments || 0}</div>
          <div className="text-xs text-emerald-400 mt-1">{metrics.confirmed_appointments || 0} confirmed active</div>
        </div>

        <div className="p-5 rounded-2xl bg-slate-900 border border-slate-800">
          <div className="text-xs text-slate-400 uppercase font-semibold">Average Call Duration</div>
          <div className="text-3xl font-extrabold text-white mt-1">{metrics.average_call_duration_seconds || 0}s</div>
          <div className="text-xs text-slate-400 mt-1">Autonomous spoken voice dialogues</div>
        </div>

        <div className="p-5 rounded-2xl bg-slate-900 border border-slate-800">
          <div className="text-xs text-slate-400 uppercase font-semibold">Human Handoffs</div>
          <div className="text-3xl font-extrabold text-white mt-1">{metrics.human_handoffs || 0}</div>
          <div className="text-xs text-purple-400 mt-1">Transferred to on-call staff</div>
        </div>
      </div>

      {/* Deep Outcome Charts & Traffic Distribution */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <div className="p-6 rounded-2xl bg-slate-900 border border-slate-800 space-y-4">
          <h3 className="font-bold text-sm text-white">Call Outcome Analysis</h3>
          <div className="space-y-3">
            {[
              { label: 'Appointments Booked', key: 'booked', color: 'bg-emerald-500' },
              { label: 'General Knowledge Resolved', key: 'inquiry_resolved', color: 'bg-teal-500' },
              { label: 'Transferred to Human Staff', key: 'transferred', color: 'bg-purple-500' },
              { label: 'Missed or Dropped Calls', key: 'missed', color: 'bg-rose-500' },
            ].map((item) => {
              const count = outcomes[item.key] || 0;
              const total = metrics.total_calls || 1;
              const pct = Math.round((count / total) * 100);
              return (
                <div key={item.key}>
                  <div className="flex justify-between text-xs mb-1">
                    <span className="text-slate-300 font-medium">{item.label}</span>
                    <span className="text-slate-400 font-mono">{count} ({pct}%)</span>
                  </div>
                  <div className="w-full h-2 rounded-full bg-slate-800 overflow-hidden">
                    <div className={`h-full ${item.color} rounded-full`} style={{ width: `${pct}%` }} />
                  </div>
                </div>
              );
            })}
          </div>
        </div>

        {/* Peak Calling Periods */}
        <div className="p-6 rounded-2xl bg-slate-900 border border-slate-800 space-y-4">
          <h3 className="font-bold text-sm text-white">Peak Inbound Calling Traffic</h3>
          <p className="text-xs text-slate-400">Distribution of calls across business hours (08:00 to 20:00)</p>

          <div className="flex items-end justify-between gap-2 h-44 pt-6">
            {peakHours.map((h: any, i: number) => {
              const maxCalls = Math.max(...peakHours.map((p: any) => p.calls), 1);
              const heightPct = Math.max(12, Math.round((h.calls / maxCalls) * 100));
              return (
                <div key={i} className="flex-1 flex flex-col items-center gap-1 h-full justify-end">
                  <div
                    className="w-full rounded-t-md bg-emerald-500/25 border border-emerald-500/40 transition-all flex items-center justify-center"
                    style={{ height: `${heightPct}%` }}
                  />
                  <span className="text-[10px] text-slate-500 font-mono">{h.hour.slice(0, 2)}</span>
                </div>
              );
            })}
          </div>
        </div>
      </div>
    </div>
  );
};
