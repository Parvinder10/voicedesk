import React, { useState, useEffect } from 'react';
import { api } from '../services/api';
import {
  Bot,
  Save,
  PhoneForwarded,
  Sparkles,
  Play,
  CheckCircle2,
  AlertCircle,
  Copy,
  Terminal,
  RefreshCw,
  PhoneIncoming,
  Headphones
} from 'lucide-react';

export const VoiceAgentPage: React.FC = () => {
  const [settings, setSettings] = useState<any>(null);
  const [greetingEn, setGreetingEn] = useState('');
  const [greetingHi, setGreetingHi] = useState('');
  const [transferPhone, setTransferPhone] = useState('');
  const [supportedLanguages, setSupportedLanguages] = useState('en,hi');
  const [promptInstructions, setPromptInstructions] = useState('');
  const [saving, setSaving] = useState(false);
  const [saveSuccess, setSaveSuccess] = useState(false);

  // Sync / Export Modal
  const [syncPayload, setSyncPayload] = useState<any>(null);
  const [isSyncModalOpen, setIsSyncModalOpen] = useState(false);

  // Live Call Simulator State
  const [simCallerPhone, setSimCallerPhone] = useState('+919811223344');
  const [simCallerName, setSimCallerName] = useState('Rohan Gupta');
  const [simScenario, setSimScenario] = useState('book'); // 'book', 'rag_inquiry', 'transfer'
  const [simLoading, setSimLoading] = useState(false);
  const [simLogs, setSimLogs] = useState<string[]>([]);

  const fetchSettings = async () => {
    try {
      const data = await api.getSettings();
      setSettings(data);
      setGreetingEn(data.ai_greeting_en || '');
      setGreetingHi(data.ai_greeting_hi || '');
      setTransferPhone(data.human_transfer_phone || '');
      setSupportedLanguages(data.supported_languages || 'en,hi');
      setPromptInstructions(data.prompt_instructions || '');
    } catch (err) {
      console.error(err);
    }
  };

  useEffect(() => {
    fetchSettings();
  }, []);

  const handleSaveSettings = async (e: React.FormEvent) => {
    e.preventDefault();
    setSaving(true);
    setSaveSuccess(false);
    try {
      await api.updateSettings({
        ai_greeting_en: greetingEn,
        ai_greeting_hi: greetingHi,
        human_transfer_phone: transferPhone,
        supported_languages: supportedLanguages,
        prompt_instructions: promptInstructions
      });
      setSaveSuccess(true);
      setTimeout(() => setSaveSuccess(false), 3000);
    } catch (err: any) {
      alert(err.message || 'Failed to update settings');
    } finally {
      setSaving(false);
    }
  };

  const handleSyncAssistant = async () => {
    try {
      const res = await api.syncAssistantConfig();
      setSyncPayload(res);
      setIsSyncModalOpen(true);
    } catch (err: any) {
      if (err.message && err.message.toLowerCase().includes('user not found')) {
        alert('Your session expired. Please sign in again to refresh your business session.');
        window.location.href = '/login';
      } else {
        alert(err.message || 'Failed to sync assistant configuration');
      }
    }
  };

  const runCallSimulation = async () => {
    setSimLoading(true);
    const logs: string[] = [];
    const addLog = (msg: string) => {
      logs.push(`[${new Date().toLocaleTimeString()}] ${msg}`);
      setSimLogs([...logs]);
    };

    try {
      const callId = `vapi_sim_${Date.now()}`;
      addLog(`Initiating incoming voice call from ${simCallerPhone} to VoiceDesk...`);

      // 1. Assistant Request
      addLog(`Sending 'assistant-request' to configure personalized greeting...`);
      const asstResp = await api.testSimulateCallWebhook({
        message: {
          type: 'assistant-request',
          call: { id: callId, customer: { number: simCallerPhone } }
        }
      });
      addLog(`AI Greeting Answered: "${asstResp.assistant?.firstMessage || 'Hello!'}"`);

      if (simScenario === 'rag_inquiry') {
        // Tool: search_knowledge_base
        addLog(`Caller asks: "What are your prices and services?"`);
        addLog(`Triggering 'search_knowledge_base' voice tool...`);
        const toolRes = await api.testSimulateCallWebhook({
          message: {
            type: 'tool-calls',
            call: { id: callId },
            toolCalls: [
              {
                id: 'tc_rag_1',
                type: 'function',
                function: {
                  name: 'search_knowledge_base',
                  arguments: { query: 'What are your prices, location, and services?' }
                }
              }
            ]
          }
        });
        const parsed = JSON.parse(toolRes.results[0].result);
        addLog(`AI Retrieved Verified Knowledge: ${parsed.answer}`);
      } else if (simScenario === 'book') {
        // Tool: identify_customer + check_availability + book_appointment
        addLog(`Checking caller history via 'identify_customer'...`);
        await api.testSimulateCallWebhook({
          message: {
            type: 'tool-calls',
            call: { id: callId },
            toolCalls: [
              {
                id: 'tc_id_1',
                type: 'function',
                function: { name: 'identify_customer', arguments: { phone: simCallerPhone } }
              }
            ]
          }
        });

        addLog(`Caller requests appointment for next available slot...`);
        const targetDate = new Date();
        targetDate.setDate(targetDate.getDate() + 3);
        const dateStr = targetDate.toISOString().split('T')[0];

        const availRes = await api.testSimulateCallWebhook({
          message: {
            type: 'tool-calls',
            call: { id: callId },
            toolCalls: [
              {
                id: 'tc_avail_1',
                type: 'function',
                function: { name: 'check_availability', arguments: { date: dateStr } }
              }
            ]
          }
        });
        const availParsed = JSON.parse(availRes.results[0].result);
        const bookedSlot = availParsed.raw_slots?.[0]?.start_time || `${dateStr}T10:00:00Z`;
        addLog(`AI Offered available slots: ${availParsed.available_slots?.slice(0, 3).join(', ')}`);

        addLog(`Booking slot at ${bookedSlot}...`);
        const bookRes = await api.testSimulateCallWebhook({
          message: {
            type: 'tool-calls',
            call: { id: callId },
            toolCalls: [
              {
                id: 'tc_book_1',
                type: 'function',
                function: {
                  name: 'book_appointment',
                  arguments: {
                    date_time: bookedSlot,
                    customer_phone: simCallerPhone,
                    customer_name: simCallerName,
                    notes: 'Simulated voice booking'
                  }
                }
              }
            ]
          }
        });
        const bookParsed = JSON.parse(bookRes.results[0].result);
        addLog(`Confirmation: ${bookParsed.message}`);
      } else if (simScenario === 'transfer') {
        addLog(`Caller: "I want to speak to a doctor right now!"`);
        addLog(`Triggering 'transfer_to_human' handoff...`);
        const transRes = await api.testSimulateCallWebhook({
          message: {
            type: 'tool-calls',
            call: { id: callId },
            toolCalls: [
              {
                id: 'tc_transfer_1',
                type: 'function',
                function: { name: 'transfer_to_human', arguments: { reason: 'Urgent human consultation requested' } }
              }
            ]
          }
        });
        const transParsed = JSON.parse(transRes.results[0].result);
        addLog(`Transfer Destination: ${transParsed.destination} (${transParsed.message})`);
      }

      // End of call report
      addLog(`Call completed naturally. Delivering 'end-of-call-report' webhook...`);
      await api.testSimulateCallWebhook({
        message: {
          type: 'end-of-call-report',
          id: `evt_sim_${Date.now()}`,
          call: {
            id: callId,
            customer: { number: simCallerPhone },
            durationSeconds: 124,
            cost: 0.16
          },
          transcript: `Caller: Hello.\nAI: Welcome to our clinic!\nCaller: Thank you.\nAI: Your request has been confirmed. Have a great day!`,
          summary: `Call simulated successfully for ${simCallerName}. Request processed and saved.`,
          analysis: {
            structuredData: {
              intent: simScenario === 'book' ? 'appointment_booking' : 'general_inquiry',
              sentiment: 'positive'
            }
          }
        }
      });
      addLog(`Call record, transcript, and summary successfully saved to PostgreSQL database! Check Call Logs.`);
    } catch (err: any) {
      addLog(`Error during simulation: ${err.message}`);
    } finally {
      setSimLoading(false);
    }
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
        <div>
          <h2 className="text-xl font-bold text-white tracking-tight">AI Voice Agent Configuration</h2>
          <p className="text-xs text-slate-400 mt-0.5">
            Configure inbound call greetings (English & Hindi), prompt rules, human escalation phone numbers, and Vapi syncing.
          </p>
        </div>

        <button
          onClick={handleSyncAssistant}
          className="px-4 py-2 rounded-xl bg-slate-900 border border-emerald-500/30 text-emerald-400 hover:bg-emerald-500/10 text-xs font-semibold transition-colors flex items-center gap-1.5"
        >
          <Sparkles className="w-4 h-4" />
          Export / Sync Vapi Assistant JSON
        </button>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Agent Persona & Configuration Form */}
        <form onSubmit={handleSaveSettings} className="bg-slate-900 border border-slate-800 rounded-2xl p-6 space-y-4">
          <div className="flex items-center justify-between pb-3 border-b border-slate-800">
            <h3 className="font-bold text-sm text-white flex items-center gap-2">
              <Bot className="w-4 h-4 text-emerald-400" />
              Greeting & Handoff Settings
            </h3>
            {saveSuccess && (
              <span className="text-xs text-emerald-400 flex items-center gap-1">
                <CheckCircle2 className="w-3.5 h-3.5" />
                Saved!
              </span>
            )}
          </div>

          <div>
            <label className="block text-xs font-medium text-slate-300 mb-1">
              English Greeting (Answer greeting)
            </label>
            <textarea
              rows={2}
              value={greetingEn}
              onChange={(e) => setGreetingEn(e.target.value)}
              placeholder="e.g. Hello! Thank you for calling..."
              className="w-full bg-slate-950 border border-slate-800 rounded-xl p-3 text-xs text-slate-100 focus:outline-none focus:border-emerald-500"
            />
          </div>

          <div>
            <label className="block text-xs font-medium text-slate-300 mb-1">
              Hindi Greeting (हिंदी अभिवादन)
            </label>
            <textarea
              rows={2}
              value={greetingHi}
              onChange={(e) => setGreetingHi(e.target.value)}
              placeholder="नमस्ते! हमारे क्लिनिक में कॉल करने के लिए धन्यवाद..."
              className="w-full bg-slate-950 border border-slate-800 rounded-xl p-3 text-xs text-slate-100 focus:outline-none focus:border-emerald-500 font-sans"
            />
          </div>

          <div className="grid grid-cols-2 gap-3">
            <div>
              <label className="block text-xs font-medium text-slate-300 mb-1">
                Human Escalation Phone Number
              </label>
              <input
                type="text"
                value={transferPhone}
                onChange={(e) => setTransferPhone(e.target.value)}
                placeholder="+919876543210"
                className="w-full bg-slate-950 border border-slate-800 rounded-xl px-3 py-2 text-xs text-slate-100 focus:outline-none focus:border-emerald-500"
              />
            </div>
            <div>
              <label className="block text-xs font-medium text-slate-300 mb-1">
                Supported Voice Languages
              </label>
              <input
                type="text"
                value={supportedLanguages}
                onChange={(e) => setSupportedLanguages(e.target.value)}
                placeholder="en,hi"
                className="w-full bg-slate-950 border border-slate-800 rounded-xl px-3 py-2 text-xs text-slate-100 focus:outline-none focus:border-emerald-500"
              />
            </div>
          </div>

          <div>
            <label className="block text-xs font-medium text-slate-300 mb-1">
              Custom Prompt Instructions / Guidelines
            </label>
            <textarea
              rows={3}
              value={promptInstructions}
              onChange={(e) => setPromptInstructions(e.target.value)}
              placeholder="e.g. Be extremely courteous, verify patient symptoms, and recommend teeth cleaning consultation."
              className="w-full bg-slate-950 border border-slate-800 rounded-xl p-3 text-xs text-slate-100 focus:outline-none focus:border-emerald-500"
            />
          </div>

          <div className="flex justify-end pt-2 border-t border-slate-800">
            <button
              type="submit"
              disabled={saving}
              className="px-4 py-2 rounded-xl bg-emerald-500 hover:bg-emerald-600 disabled:opacity-50 text-slate-950 font-bold text-xs flex items-center gap-1.5 shadow-lg shadow-emerald-500/10"
            >
              <Save className="w-4 h-4" />
              {saving ? 'Saving...' : 'Save Agent Persona'}
            </button>
          </div>
        </form>

        {/* Live Call Simulator Panel */}
        <div className="bg-slate-900 border border-slate-800 rounded-2xl p-6 space-y-4 flex flex-col justify-between">
          <div>
            <div className="flex items-center justify-between pb-3 border-b border-slate-800">
              <h3 className="font-bold text-sm text-white flex items-center gap-2">
                <Play className="w-4 h-4 text-emerald-400" />
                Live Inbound Call Simulator
              </h3>
              <span className="text-[11px] text-emerald-400 font-mono">End-to-End Test Engine</span>
            </div>

            <p className="text-xs text-slate-400 mt-2">
              Test your configured receptionist without needing a real telephone line. Executes genuine backend Vapi webhooks, tool calls, and database updates.
            </p>

            <div className="grid grid-cols-2 gap-3 mt-4">
              <div>
                <label className="block text-xs font-medium text-slate-300 mb-1">Caller Phone</label>
                <input
                  type="text"
                  value={simCallerPhone}
                  onChange={(e) => setSimCallerPhone(e.target.value)}
                  className="w-full bg-slate-950 border border-slate-800 rounded-xl px-3 py-2 text-xs text-slate-100 focus:outline-none focus:border-emerald-500"
                />
              </div>
              <div>
                <label className="block text-xs font-medium text-slate-300 mb-1">Caller Name</label>
                <input
                  type="text"
                  value={simCallerName}
                  onChange={(e) => setSimCallerName(e.target.value)}
                  className="w-full bg-slate-950 border border-slate-800 rounded-xl px-3 py-2 text-xs text-slate-100 focus:outline-none focus:border-emerald-500"
                />
              </div>
            </div>

            <div className="mt-3">
              <label className="block text-xs font-medium text-slate-300 mb-1">Select Test Scenario</label>
              <select
                value={simScenario}
                onChange={(e) => setSimScenario(e.target.value)}
                className="w-full bg-slate-950 border border-slate-800 rounded-xl px-3 py-2 text-xs text-slate-100 focus:outline-none focus:border-emerald-500"
              >
                <option value="book">Appointment Inquiry & Booking Workflow</option>
                <option value="rag_inquiry">Pricing & Knowledge Base (RAG) Inquiry</option>
                <option value="transfer">Human Handoff Escalation Request</option>
              </select>
            </div>

            <button
              type="button"
              onClick={runCallSimulation}
              disabled={simLoading}
              className="w-full mt-4 py-2.5 px-4 rounded-xl bg-gradient-to-r from-emerald-500 to-teal-500 hover:from-emerald-600 hover:to-teal-600 disabled:opacity-50 text-slate-950 font-bold text-xs flex items-center justify-center gap-2 shadow-lg shadow-emerald-500/10"
            >
              <PhoneIncoming className="w-4 h-4" />
              {simLoading ? 'Simulating Call Inbound Execution...' : 'Run Inbound Test Call'}
            </button>
          </div>

          {/* Console Output */}
          <div className="mt-4 p-3 rounded-xl bg-slate-950 border border-slate-800 font-mono text-[11px] text-slate-300 h-44 overflow-y-auto space-y-1">
            {simLogs.length === 0 ? (
              <span className="text-slate-600">Simulator logs will appear here during execution...</span>
            ) : (
              simLogs.map((log, i) => (
                <div key={i} className="leading-tight text-emerald-400">
                  {log}
                </div>
              ))
            )}
          </div>
        </div>
      </div>

      {/* Vapi Sync Payload Modal */}
      {isSyncModalOpen && syncPayload && (
        <div className="fixed inset-0 z-50 bg-black/75 backdrop-blur-sm flex items-center justify-center p-4">
          <div className="bg-slate-900 border border-slate-800 rounded-2xl max-w-2xl w-full p-6 space-y-4 max-h-[85vh] overflow-y-auto">
            <div className="flex items-center justify-between pb-3 border-b border-slate-800">
              <h3 className="font-bold text-base text-white">Vapi Assistant Production Configuration</h3>
              <button onClick={() => setIsSyncModalOpen(false)} className="text-slate-400 hover:text-white">✕</button>
            </div>

            <p className="text-xs text-slate-400">
              Copy this JSON into your Vapi Dashboard or use the Vapi API to deploy your voice assistant with all 10 registered backend tools:
            </p>

            <div className="p-3 bg-slate-950 border border-slate-800 rounded-xl font-mono text-[11px] text-emerald-400 overflow-x-auto max-h-80">
              <pre>{JSON.stringify(syncPayload, null, 2)}</pre>
            </div>

            <div className="flex justify-end pt-2">
              <button
                onClick={() => {
                  navigator.clipboard.writeText(JSON.stringify(syncPayload, null, 2));
                  alert('Copied to clipboard!');
                }}
                className="px-4 py-2 rounded-xl bg-emerald-500 text-slate-950 font-bold text-xs flex items-center gap-1.5"
              >
                <Copy className="w-3.5 h-3.5" />
                Copy Assistant JSON
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
