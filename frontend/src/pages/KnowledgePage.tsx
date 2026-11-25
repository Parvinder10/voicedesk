import React, { useState, useEffect } from 'react';
import { api } from '../services/api';
import {
  BookOpen,
  Upload,
  FileText,
  Search,
  Trash2,
  RefreshCw,
  Sparkles,
  CheckCircle2,
  AlertCircle,
  HelpCircle,
  FileCheck,
  Send
} from 'lucide-react';

export const KnowledgePage: React.FC = () => {
  const [documents, setDocuments] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [uploading, setUploading] = useState(false);
  const [uploadError, setUploadError] = useState<string | null>(null);

  // RAG Query Simulator State
  const [testQuery, setTestQuery] = useState('');
  const [queryLoading, setQueryLoading] = useState(false);
  const [queryResult, setQueryResult] = useState<any>(null);

  const fetchDocuments = async () => {
    try {
      setLoading(true);
      const data = await api.getDocuments();
      setDocuments(data);
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchDocuments();
  }, []);

  const handleFileUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;

    setUploading(true);
    setUploadError(null);
    try {
      await api.uploadDocument(file);
      fetchDocuments();
    } catch (err: any) {
      setUploadError(err.message || 'Failed to process document');
    } finally {
      setUploading(false);
      e.target.value = '';
    }
  };

  const handleUploadDemoDoc = async () => {
    setUploading(true);
    setUploadError(null);
    try {
      const demoContent = `# Official Clinic Guidelines & Pricing
We specialize in restorative dental surgery, teeth whitening, and general hygiene.
Teeth whitening procedure is priced at 4500 INR with a duration of 45 minutes.
Root canal treatment ranges from 3500 to 5000 INR depending on tooth condition.
Digital X-Ray diagnostics are complimentary with every major procedure.
We are located at Suite 402, Pinnacle Plaza, Bandra West.
Free underground parking is available for all confirmed patients.
Cancellation policy: Please notify us at least 4 hours before your slot to avoid cancellation fees.
Emergency helpline: +919876543210.
`;
      const blob = new Blob([demoContent], { type: 'text/plain' });
      const file = new File([blob], 'Clinic_Pricing_and_Policies_Guide.txt', { type: 'text/plain' });
      await api.uploadDocument(file);
      fetchDocuments();
    } catch (err: any) {
      setUploadError(err.message || 'Failed to upload demo document');
    } finally {
      setUploading(false);
    }
  };

  const handleDelete = async (id: string) => {
    if (confirm('Delete this document and purge its vector chunks?')) {
      try {
        await api.deleteDocument(id);
        fetchDocuments();
      } catch (err: any) {
        alert(err.message || 'Failed to delete');
      }
    }
  };

  const handleTestQuery = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!testQuery.trim()) return;

    setQueryLoading(true);
    try {
      const res = await api.queryKnowledge(testQuery);
      setQueryResult(res);
    } catch (err: any) {
      alert(err.message || 'Query failed');
    } finally {
      setQueryLoading(false);
    }
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
        <div>
          <h2 className="text-xl font-bold text-white tracking-tight">RAG Knowledge Assistant</h2>
          <p className="text-xs text-slate-400 mt-0.5">
            Upload PDFs, FAQs, and pricing documents. The AI receptionist answers caller questions strictly grounded in your verified documents.
          </p>
        </div>

        <div className="flex items-center gap-2">
          <button
            onClick={handleUploadDemoDoc}
            disabled={uploading}
            className="px-3 py-2 rounded-xl bg-slate-900 border border-emerald-500/30 text-emerald-400 hover:bg-emerald-500/10 text-xs font-semibold transition-colors flex items-center gap-1.5"
          >
            <Sparkles className="w-3.5 h-3.5" />
            Upload Demo Knowledge Document
          </button>

          <label className="px-4 py-2 rounded-xl bg-emerald-500 hover:bg-emerald-600 cursor-pointer text-slate-950 font-semibold text-xs transition-colors flex items-center gap-1.5 shadow-lg shadow-emerald-500/10">
            <Upload className="w-4 h-4" />
            <span>{uploading ? 'Processing & Indexing...' : 'Upload PDF or TXT'}</span>
            <input
              type="file"
              accept=".pdf,.txt,.md"
              onChange={handleFileUpload}
              disabled={uploading}
              className="hidden"
            />
          </label>
        </div>
      </div>

      {uploadError && (
        <div className="p-3 rounded-xl bg-rose-500/10 border border-rose-500/20 text-rose-400 text-xs flex items-center gap-2">
          <AlertCircle className="w-4 h-4 shrink-0" />
          <span>{uploadError}</span>
        </div>
      )}

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Document List */}
        <div className="lg:col-span-2 bg-slate-900 border border-slate-800 rounded-2xl p-6 space-y-4">
          <div className="flex items-center justify-between pb-3 border-b border-slate-800">
            <h3 className="font-bold text-sm text-white flex items-center gap-2">
              <FileCheck className="w-4 h-4 text-emerald-400" />
              Indexed Documents ({documents.length})
            </h3>
            <span className="text-xs text-slate-400 font-mono">Isolated to current organization</span>
          </div>

          {loading ? (
            <div className="p-8 text-center text-xs text-slate-400">Loading documents...</div>
          ) : documents.length === 0 ? (
            <div className="p-12 text-center text-slate-500 text-xs">
              <BookOpen className="w-8 h-8 mx-auto mb-2 text-slate-600" />
              No documents uploaded yet. Click "Upload Demo Knowledge Document" to test instantly!
            </div>
          ) : (
            <div className="divide-y divide-slate-800/80">
              {documents.map((doc) => (
                <div key={doc.id} className="py-4 flex items-center justify-between gap-4 text-xs">
                  <div className="flex items-center gap-3">
                    <div className="p-2.5 rounded-xl bg-slate-800 text-emerald-400">
                      <FileText className="w-4 h-4" />
                    </div>
                    <div>
                      <div className="font-bold text-slate-100">{doc.filename}</div>
                      <div className="text-[11px] text-slate-400 font-mono mt-0.5 flex items-center gap-2">
                        <span>{doc.chunk_count} semantic vector chunks</span>
                        <span>•</span>
                        <span>{(doc.file_size_bytes / 1024).toFixed(1)} KB</span>
                        <span>•</span>
                        <span className="text-emerald-400 font-semibold uppercase">{doc.status}</span>
                      </div>
                    </div>
                  </div>

                  <div className="flex items-center gap-2">
                    <button
                      onClick={() => handleDelete(doc.id)}
                      className="p-1.5 text-slate-500 hover:text-rose-400 rounded-lg hover:bg-rose-500/10"
                      title="Delete document and chunks"
                    >
                      <Trash2 className="w-3.5 h-3.5" />
                    </button>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>

        {/* Live RAG Retrieval Simulator */}
        <div className="bg-slate-900 border border-slate-800 rounded-2xl p-6 space-y-4">
          <div className="flex items-center justify-between pb-3 border-b border-slate-800">
            <h3 className="font-bold text-sm text-white flex items-center gap-2">
              <Search className="w-4 h-4 text-emerald-400" />
              Live Semantic Query Tester
            </h3>
          </div>

          <p className="text-xs text-slate-400">
            Simulate what the AI voice receptionist will answer when a caller asks a specific question.
          </p>

          <form onSubmit={handleTestQuery} className="space-y-3">
            <div>
              <input
                type="text"
                value={testQuery}
                onChange={(e) => setTestQuery(e.target.value)}
                placeholder="e.g. How much does teeth whitening cost?"
                className="w-full bg-slate-950 border border-slate-800 rounded-xl px-3 py-2 text-xs text-slate-100 focus:outline-none focus:border-emerald-500"
              />
            </div>
            <button
              type="submit"
              disabled={queryLoading}
              className="w-full py-2 px-3 rounded-xl bg-emerald-500 hover:bg-emerald-600 disabled:opacity-50 text-slate-950 font-bold text-xs transition-colors flex items-center justify-center gap-1.5 shadow-lg shadow-emerald-500/10"
            >
              <Send className="w-3.5 h-3.5" />
              {queryLoading ? 'Retrieving Answer...' : 'Ask Knowledge Base'}
            </button>
          </form>

          {/* Result Box */}
          {queryResult && (
            <div className="p-4 rounded-xl bg-slate-950 border border-slate-800 space-y-3 text-xs">
              <div className="flex items-center justify-between">
                <span className="text-[10px] font-bold uppercase text-slate-500">Grounded AI Answer</span>
                <span className={`text-[10px] font-semibold px-2 py-0.5 rounded-full ${
                  queryResult.has_answer ? 'bg-emerald-500/10 text-emerald-400 border border-emerald-500/20' : 'bg-rose-500/10 text-rose-400 border border-rose-500/20'
                }`}>
                  {queryResult.has_answer ? 'Verified Grounded Answer' : 'Limitation Acknowledged'}
                </span>
              </div>

              <p className="text-slate-200 leading-relaxed font-sans">{queryResult.answer}</p>

              {queryResult.sources.length > 0 && (
                <div className="pt-2 border-t border-slate-800 space-y-1.5">
                  <span className="text-[10px] font-bold uppercase text-slate-500">Source References</span>
                  {queryResult.sources.map((s: any, idx: number) => (
                    <div key={idx} className="p-2 rounded-lg bg-slate-900 border border-slate-850 text-[11px]">
                      <div className="flex justify-between text-slate-400">
                        <span className="font-semibold text-slate-300">{s.filename}</span>
                        <span className="font-mono text-emerald-400">score: {s.score}</span>
                      </div>
                      <p className="text-slate-400 italic mt-0.5">"{s.snippet}"</p>
                    </div>
                  ))}
                </div>
              )}
            </div>
          )}
        </div>
      </div>
    </div>
  );
};
