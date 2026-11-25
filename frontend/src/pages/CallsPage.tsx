import React, { useState, useEffect } from 'react';
import { api } from '../services/api';
import {
  PhoneCall,
  PhoneIncoming,
  Clock,
  User,
  FileText,
  Volume2,
  Filter,
  ArrowRight,
  Headphones,
  CheckCircle2,
  AlertTriangle,
  Play,
  RotateCcw
} from 'lucide-react';

export const CallsPage: React.FC = () => {
  const [calls, setCalls] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [outcomeFilter, setOutcomeFilter] = useState('');
  const [selectedCall, setSelectedCall] = useState<any>(null);
  const [transcriptData, setTranscriptData] = useState<any>(null);
  const [loadingTranscript, setLoadingTranscript] = useState(false);

  const fetchCalls = async () => {
    try {
      setLoading(true);
      const data = await api.getCalls({ outcome: outcomeFilter || undefined });
      setCalls(data);
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchCalls();
  }, [outcomeFilter]);

  const openCallDetails = async (call: any) => {
    setSelectedCall(call);
    try {
      setLoadingTranscript(true);
      const t = await api.getCallTranscript(call.id);
      setTranscriptData(t);
    } catch (err) {
      setTranscriptData(null);
    } finally {
      setLoadingTranscript(false);
    }
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
        <div>
          <h2 className="text-xl font-bold text-white tracking-tight">Call Intelligence & Transcripts</h2>
          <p className="text-xs text-slate-400 mt-0.5">
            Full audit logs of all inbound voice calls, AI conversation turns, sentiment analysis, and summaries.
          </p>
        </div>

        <div className="flex items-center gap-2">
          <Filter className="w-3.5 h-3.5 text-slate-400" />
          <select
            value={outcomeFilter}
            onChange={(e) => setOutcomeFilter(e.target.value)}
            className="bg-slate-900 border border-slate-800 rounded-xl px-3 py-1.5 text-xs text-slate-300 focus:outline-none"
          >
            <option value="">All Call Outcomes</option>
            <option value="booked">Appointment Booked</option>
            <option value="inquiry_resolved">Inquiry Resolved (RAG)</option>
            <option value="transferred">Transferred to Human</option>
            <option value="missed">Missed / Dropped</option>
          </select>
        </div>
      </div>

      {/* Calls List */}
      <div className="bg-slate-900 border border-slate-800 rounded-2xl overflow-hidden">
        {loading ? (
          <div className="p-8 text-center text-xs text-slate-400">Loading call intelligence records...</div>
        ) : calls.length === 0 ? (
          <div className="p-12 text-center text-slate-500 text-xs">
            <PhoneCall className="w-8 h-8 mx-auto mb-2 text-slate-600" />
            No voice calls logged yet. You can simulate or make test calls in the "Voice Agent" tab!
          </div>
        ) : (
          <div className="divide-y divide-slate-800/80">
            {calls.map((call) => (
              <div
                key={call.id}
                onClick={() => openCallDetails(call)}
                className="p-4 sm:p-5 flex flex-col md:flex-row items-start md:items-center justify-between gap-4 hover:bg-slate-850/50 cursor-pointer transition-colors"
              >
                <div className="flex items-start gap-4">
                  <div className={`p-3 rounded-2xl ${
                    call.outcome === 'booked' ? 'bg-emerald-500/10 text-emerald-400 border border-emerald-500/20' :
                    call.outcome === 'transferred' ? 'bg-purple-500/10 text-purple-400 border border-purple-500/20' :
                    call.outcome === 'missed' ? 'bg-rose-500/10 text-rose-400 border border-rose-500/20' :
                    'bg-blue-500/10 text-blue-400 border border-blue-500/20'
                  }`}>
                    <PhoneIncoming className="w-4 h-4" />
                  </div>

                  <div>
                    <div className="flex items-center gap-2">
                      <span className="font-bold text-sm text-slate-100">{call.caller_phone}</span>
                      {call.customer_name && (
                        <span className="text-xs text-emerald-400 font-medium">({call.customer_name})</span>
                      )}
                      <span className={`text-[10px] font-semibold px-2 py-0.5 rounded-full border ${
                        call.outcome === 'booked' ? 'bg-emerald-500/10 text-emerald-400 border-emerald-500/20' :
                        call.outcome === 'transferred' ? 'bg-purple-500/10 text-purple-400 border-purple-500/20' :
                        call.outcome === 'missed' ? 'bg-rose-500/10 text-rose-400 border-rose-500/20' :
                        'bg-slate-800 text-slate-300 border-slate-700'
                      }`}>
                        {call.outcome}
                      </span>
                    </div>

                    <div className="text-xs text-slate-400 mt-1 line-clamp-1">
                      {call.summary_text || 'Inbound reception call handled by AI assistant.'}
                    </div>

                    <div className="flex items-center gap-4 text-[11px] text-slate-500 font-mono mt-2">
                      <span className="flex items-center gap-1">
                        <Clock className="w-3 h-3 text-slate-600" />
                        {call.duration_seconds}s duration
                      </span>
                      {call.sentiment && (
                        <span className="text-slate-400">Sentiment: {call.sentiment}</span>
                      )}
                      {call.escalation_status === 'requested' && (
                        <span className="text-purple-400">Transferred to: {call.transfer_phone_number}</span>
                      )}
                    </div>
                  </div>
                </div>

                <div className="text-right flex items-center gap-3 self-end md:self-auto">
                  <span className="text-[11px] font-mono text-slate-500">
                    {new Date(call.created_at).toLocaleString([], { dateStyle: 'short', timeStyle: 'short' })}
                  </span>
                  <div className="p-2 rounded-xl bg-slate-800 text-slate-400 group-hover:text-emerald-400">
                    <ArrowRight className="w-3.5 h-3.5" />
                  </div>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>

      {/* Transcript & Intelligence Detail Modal */}
      {selectedCall && (
        <div className="fixed inset-0 z-50 bg-black/75 backdrop-blur-sm flex items-center justify-center p-4">
          <div className="bg-slate-900 border border-slate-800 rounded-2xl max-w-2xl w-full p-6 space-y-5 max-h-[85vh] overflow-y-auto">
            <div className="flex items-center justify-between pb-3 border-b border-slate-800">
              <div>
                <h3 className="font-bold text-base text-white flex items-center gap-2">
                  Call Record: {selectedCall.caller_phone}
                </h3>
                <span className="text-xs text-slate-400 font-mono">
                  {new Date(selectedCall.created_at).toLocaleString()} • {selectedCall.duration_seconds}s
                </span>
              </div>
              <button onClick={() => setSelectedCall(null)} className="text-slate-400 hover:text-white">✕</button>
            </div>

            {/* AI Summary Card */}
            {selectedCall.summary_text && (
              <div className="p-4 rounded-xl bg-slate-950 border border-slate-800/80 space-y-1">
                <span className="text-[11px] font-bold uppercase tracking-wider text-emerald-400 flex items-center gap-1">
                  <FileText className="w-3.5 h-3.5" />
                  AI Call Summary
                </span>
                <p className="text-xs text-slate-300 leading-relaxed">{selectedCall.summary_text}</p>
                {selectedCall.intent && (
                  <div className="text-[11px] text-slate-500 pt-1 font-mono">Intent: {selectedCall.intent}</div>
                )}
              </div>
            )}

            {/* Audio Recording Player Simulation */}
            {selectedCall.recording_url && (
              <div className="p-3 rounded-xl bg-slate-850 border border-slate-800 flex items-center justify-between">
                <div className="flex items-center gap-2 text-xs text-slate-300">
                  <Volume2 className="w-4 h-4 text-emerald-400" />
                  <span>Call Recording URL Attached</span>
                </div>
                <a
                  href={selectedCall.recording_url}
                  target="_blank"
                  rel="noreferrer"
                  className="text-xs text-emerald-400 underline hover:text-emerald-300"
                >
                  Download Audio
                </a>
              </div>
            )}

            {/* Full Transcript */}
            <div>
              <h4 className="text-xs font-bold uppercase text-slate-400 mb-2">Full Call Transcript</h4>
              {loadingTranscript ? (
                <div className="p-4 text-center text-xs text-slate-500">Loading transcript...</div>
              ) : transcriptData ? (
                <div className="p-4 rounded-xl bg-slate-950 border border-slate-800 font-mono text-xs text-slate-300 leading-relaxed whitespace-pre-wrap max-h-60 overflow-y-auto">
                  {transcriptData.full_transcript}
                </div>
              ) : (
                <div className="p-4 text-center text-xs text-slate-500">
                  No full transcript text captured for this call.
                </div>
              )}
            </div>

            <div className="flex justify-end pt-2 border-t border-slate-800">
              <button
                onClick={() => setSelectedCall(null)}
                className="px-4 py-2 rounded-xl bg-slate-800 text-xs font-medium text-slate-200"
              >
                Close
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
