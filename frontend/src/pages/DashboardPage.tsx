import React, { useEffect, useState } from 'react';
import { api } from '../services/api';
import { useAuth } from '../contexts/AuthContext';
import { Link } from 'react-router-dom';
import {
  PhoneCall,
  Calendar,
  CheckCircle2,
  Clock,
  ArrowUpRight,
  TrendingUp,
  UserCheck,
  Headphones,
  FileText,
  Activity,
  Bot,
  AlertTriangle,
  Play,
  Sparkles
} from 'lucide-react';

export const DashboardPage: React.FC = () => {
  const { organization } = useAuth();
  const [data, setData] = useState<any>(null);
  const [activity, setActivity] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const fetchDashboardData = async () => {
    try {
      setLoading(true);
      const [overviewData, activityData] = await Promise.all([
        api.getDashboardOverview(),
        api.getDashboardActivity(10)
      ]);
      setData(overviewData);
      setActivity(activityData);
    } catch (err: any) {
      setError(err.message || 'Failed to load dashboard metrics');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchDashboardData();
  }, []);

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-[400px]">
        <div className="flex flex-col items-center gap-3">
          <div className="w-8 h-8 border-3 border-emerald-500 border-t-transparent rounded-full animate-spin" />
          <p className="text-sm text-slate-400">Loading live receptionist metrics...</p>
        </div>
      </div>
    );
  }

  const metrics = data?.metrics || {};
  const outcomes = data?.outcomes_breakdown || {};
  const peakHours = data?.peak_calling_hours || [];

  return (
    <div className="space-y-6">
      {/* Top Welcome Banner */}
      <div className="p-6 rounded-2xl bg-gradient-to-r from-slate-900 via-slate-850 to-slate-900 border border-slate-800 flex flex-col md:flex-row items-start md:items-center justify-between gap-4">
        <div>
          <div className="flex items-center gap-2">
            <h2 className="text-xl font-bold text-white tracking-tight">{organization?.name}</h2>
            <span className="px-2 py-0.5 rounded-full text-[11px] font-semibold bg-emerald-500/20 text-emerald-400 border border-emerald-500/30">
              Active Voice Receptionist
            </span>
          </div>
          <p className="text-xs text-slate-400 mt-1">
            Real-time multi-tenant dashboard. All metrics are computed dynamically from actual database records.
          </p>
        </div>
        <div className="flex items-center gap-2">
          <Link
            to="/voice-agent"
            className="px-4 py-2 rounded-xl bg-emerald-500 hover:bg-emerald-600 text-slate-950 font-semibold text-xs transition-colors flex items-center gap-1.5 shadow-lg shadow-emerald-500/10"
          >
            <Bot className="w-4 h-4" />
            Test Inbound Call
          </Link>
          <Link
            to="/appointments"
            className="px-4 py-2 rounded-xl bg-slate-800 hover:bg-slate-700 text-slate-200 font-semibold text-xs transition-colors flex items-center gap-1.5"
          >
            <Calendar className="w-4 h-4" />
            View Calendar
          </Link>
        </div>
      </div>

      {/* KPI Cards Grid */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        {/* Total Calls */}
        <div className="p-5 rounded-2xl bg-slate-900 border border-slate-800 flex flex-col justify-between">
          <div className="flex items-center justify-between text-slate-400 mb-2">
            <span className="text-xs font-semibold uppercase tracking-wider">Inbound Calls</span>
            <div className="p-2 rounded-xl bg-blue-500/10 text-blue-400">
              <PhoneCall className="w-4 h-4" />
            </div>
          </div>
          <div className="text-2xl font-extrabold text-white">{metrics.total_calls || 0}</div>
          <div className="text-xs text-slate-400 mt-1 flex items-center gap-1">
            <span className="text-emerald-400 font-medium">{metrics.answered_calls || 0} answered</span>
            <span>•</span>
            <span className="text-rose-400 font-medium">{metrics.missed_calls || 0} missed</span>
          </div>
        </div>

        {/* Confirmed Appointments */}
        <div className="p-5 rounded-2xl bg-slate-900 border border-slate-800 flex flex-col justify-between">
          <div className="flex items-center justify-between text-slate-400 mb-2">
            <span className="text-xs font-semibold uppercase tracking-wider">Booked Appointments</span>
            <div className="p-2 rounded-xl bg-emerald-500/10 text-emerald-400">
              <Calendar className="w-4 h-4" />
            </div>
          </div>
          <div className="text-2xl font-extrabold text-white">{metrics.total_appointments || 0}</div>
          <div className="text-xs text-slate-400 mt-1 flex items-center gap-1">
            <span className="text-emerald-400 font-medium">{metrics.confirmed_appointments || 0} confirmed</span>
            <span>•</span>
            <span className="text-amber-400 font-medium">{metrics.rescheduled_appointments || 0} resched</span>
          </div>
        </div>

        {/* Resolution Rate */}
        <div className="p-5 rounded-2xl bg-slate-900 border border-slate-800 flex flex-col justify-between">
          <div className="flex items-center justify-between text-slate-400 mb-2">
            <span className="text-xs font-semibold uppercase tracking-wider">Resolution Rate</span>
            <div className="p-2 rounded-xl bg-teal-500/10 text-teal-400">
              <TrendingUp className="w-4 h-4" />
            </div>
          </div>
          <div className="text-2xl font-extrabold text-white">{metrics.resolution_rate_percentage || 100}%</div>
          <div className="text-xs text-slate-400 mt-1">
            AI resolved inquiries & bookings autonomously
          </div>
        </div>

        {/* Human Handoffs */}
        <div className="p-5 rounded-2xl bg-slate-900 border border-slate-800 flex flex-col justify-between">
          <div className="flex items-center justify-between text-slate-400 mb-2">
            <span className="text-xs font-semibold uppercase tracking-wider">Human Handoffs</span>
            <div className="p-2 rounded-xl bg-purple-500/10 text-purple-400">
              <Headphones className="w-4 h-4" />
            </div>
          </div>
          <div className="text-2xl font-extrabold text-white">{metrics.human_handoffs || 0}</div>
          <div className="text-xs text-slate-400 mt-1">
            Avg duration: {metrics.average_call_duration_seconds || 0}s
          </div>
        </div>
      </div>

      {/* Middle Row: Calling Outcomes + Peak Calling Hours */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Call Outcomes Breakdown */}
        <div className="p-6 rounded-2xl bg-slate-900 border border-slate-800">
          <div className="flex items-center justify-between mb-4">
            <h3 className="text-sm font-bold text-white">Inbound Call Outcomes</h3>
            <span className="text-xs text-slate-400">Classified by VoiceDesk AI</span>
          </div>
          <div className="space-y-3">
            {[
              { label: 'Appointment Booked', key: 'booked', color: 'bg-emerald-500' },
              { label: 'Inquiry Resolved (RAG)', key: 'inquiry_resolved', color: 'bg-teal-500' },
              { label: 'Transferred to Staff', key: 'transferred', color: 'bg-purple-500' },
              { label: 'Cancelled / Rescheduled', key: 'cancelled', color: 'bg-amber-500' },
              { label: 'Missed / Dropped', key: 'missed', color: 'bg-rose-500' }
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
                    <div
                      className={`h-full ${item.color} rounded-full transition-all duration-500`}
                      style={{ width: `${pct}%` }}
                    />
                  </div>
                </div>
              );
            })}
          </div>
        </div>

        {/* Peak Calling Hours Chart */}
        <div className="p-6 rounded-2xl bg-slate-900 border border-slate-800">
          <div className="flex items-center justify-between mb-4">
            <h3 className="text-sm font-bold text-white">Peak Calling Periods</h3>
            <span className="text-xs text-slate-400 font-mono">08:00 — 20:00</span>
          </div>
          <div className="flex items-end justify-between gap-1.5 h-44 pt-6">
            {peakHours.map((h: any, i: number) => {
              const maxCalls = Math.max(...peakHours.map((p: any) => p.calls), 1);
              const heightPct = Math.max(12, Math.round((h.calls / maxCalls) * 100));
              return (
                <div key={i} className="flex-1 flex flex-col items-center gap-1.5 h-full justify-end">
                  <div
                    className="w-full rounded-t-md bg-emerald-500/20 hover:bg-emerald-500/40 border border-emerald-500/40 transition-all flex items-center justify-center group relative cursor-pointer"
                    style={{ height: `${heightPct}%` }}
                  >
                    <span className="absolute -top-7 text-[10px] bg-slate-800 text-white px-1.5 py-0.5 rounded opacity-0 group-hover:opacity-100 transition-opacity whitespace-nowrap">
                      {h.calls} calls
                    </span>
                  </div>
                  <span className="text-[10px] text-slate-500 font-mono">{h.hour.slice(0, 2)}</span>
                </div>
              );
            })}
          </div>
        </div>
      </div>

      {/* Unified Live Activity Stream */}
      <div className="p-6 rounded-2xl bg-slate-900 border border-slate-800">
        <div className="flex items-center justify-between mb-4">
          <div className="flex items-center gap-2">
            <Activity className="w-4 h-4 text-emerald-400" />
            <h3 className="text-sm font-bold text-white">Live Activity Stream</h3>
          </div>
          <span className="text-xs text-slate-400">Calls & Booking Events</span>
        </div>

        {activity.length === 0 ? (
          <div className="py-8 text-center text-slate-500 text-xs">
            No recent activity recorded yet. Inbound calls and bookings will appear here in real-time.
          </div>
        ) : (
          <div className="divide-y divide-slate-800/60">
            {activity.map((item, idx) => (
              <div key={idx} className="py-3 flex items-center justify-between text-xs">
                <div className="flex items-center gap-3">
                  <div className={`p-2 rounded-xl ${item.type === 'call' ? 'bg-blue-500/10 text-blue-400' : 'bg-emerald-500/10 text-emerald-400'}`}>
                    {item.type === 'call' ? <PhoneCall className="w-3.5 h-3.5" /> : <Calendar className="w-3.5 h-3.5" />}
                  </div>
                  <div>
                    <div className="font-semibold text-slate-200">{item.title}</div>
                    <div className="text-slate-400 text-[11px] mt-0.5">{item.subtitle}</div>
                  </div>
                </div>
                <div className="text-right">
                  <span className="text-[11px] font-mono text-slate-500">
                    {item.timestamp ? new Date(item.timestamp).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }) : ''}
                  </span>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
};
