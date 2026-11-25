import React, { useState, useEffect } from 'react';
import { api } from '../services/api';
import {
  Users,
  Search,
  Plus,
  Phone,
  Mail,
  Calendar,
  Clock,
  FileText,
  ChevronRight,
  UserCheck
} from 'lucide-react';

export const CustomersPage: React.FC = () => {
  const [customers, setCustomers] = useState<any[]>([]);
  const [search, setSearch] = useState('');
  const [loading, setLoading] = useState(true);
  const [selectedCustomerId, setSelectedCustomerId] = useState<string | null>(null);
  const [customerDetail, setCustomerDetail] = useState<any>(null);
  const [loadingDetail, setLoadingDetail] = useState(false);

  // New Customer Modal
  const [isCreateOpen, setIsCreateOpen] = useState(false);
  const [name, setName] = useState('');
  const [phone, setPhone] = useState('');
  const [email, setEmail] = useState('');
  const [notes, setNotes] = useState('');
  const [createError, setCreateError] = useState<string | null>(null);

  const fetchCustomers = async () => {
    try {
      setLoading(true);
      const data = await api.getCustomers(search);
      setCustomers(data);
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    const delayDebounce = setTimeout(() => {
      fetchCustomers();
    }, 250);
    return () => clearTimeout(delayDebounce);
  }, [search]);

  const handleSelectCustomer = async (id: string) => {
    setSelectedCustomerId(id);
    try {
      setLoadingDetail(true);
      const detail = await api.getCustomer(id);
      setCustomerDetail(detail);
    } catch (err) {
      console.error(err);
    } finally {
      setLoadingDetail(false);
    }
  };

  const handleCreateCustomer = async (e: React.FormEvent) => {
    e.preventDefault();
    setCreateError(null);
    try {
      await api.createCustomer({ name, phone, email: email || null, notes: notes || null });
      setIsCreateOpen(false);
      setName('');
      setPhone('');
      setEmail('');
      setNotes('');
      fetchCustomers();
    } catch (err: any) {
      setCreateError(err.message || 'Failed to create customer');
    }
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
        <div>
          <h2 className="text-xl font-bold text-white tracking-tight">Customer Directory</h2>
          <p className="text-xs text-slate-400 mt-0.5">
            Caller phone identification profiles, notes, past calls, and appointment records.
          </p>
        </div>

        <button
          onClick={() => setIsCreateOpen(true)}
          className="px-4 py-2 rounded-xl bg-emerald-500 hover:bg-emerald-600 text-slate-950 font-semibold text-xs transition-colors flex items-center gap-1.5 shadow-lg shadow-emerald-500/10"
        >
          <Plus className="w-4 h-4" />
          Add Customer
        </button>
      </div>

      {/* Search Input */}
      <div className="relative max-w-md">
        <Search className="w-4 h-4 text-slate-500 absolute left-3 top-3" />
        <input
          type="text"
          value={search}
          onChange={(e) => setSearch(e.target.value)}
          placeholder="Search by name, phone (+91...) or email..."
          className="w-full bg-slate-900 border border-slate-800 rounded-xl pl-9 pr-3 py-2.5 text-xs text-slate-100 placeholder-slate-500 focus:outline-none focus:border-emerald-500 transition-colors"
        />
      </div>

      {/* Customers List & Detail Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Table / List */}
        <div className="lg:col-span-2 bg-slate-900 border border-slate-800 rounded-2xl overflow-hidden">
          {loading ? (
            <div className="p-8 text-center text-xs text-slate-400">Loading customer records...</div>
          ) : customers.length === 0 ? (
            <div className="p-12 text-center text-slate-500 text-xs">
              <Users className="w-8 h-8 mx-auto mb-2 text-slate-600" />
              No customers found. As callers call VoiceDesk, their profiles are identified automatically.
            </div>
          ) : (
            <div className="divide-y divide-slate-800/80">
              {customers.map((c) => (
                <div
                  key={c.id}
                  onClick={() => handleSelectCustomer(c.id)}
                  className={`p-4 flex items-center justify-between hover:bg-slate-850/60 cursor-pointer transition-colors ${
                    selectedCustomerId === c.id ? 'bg-slate-850 border-l-2 border-emerald-500' : ''
                  }`}
                >
                  <div className="flex items-center gap-3">
                    <div className="w-9 h-9 rounded-full bg-slate-800 text-emerald-400 flex items-center justify-center font-bold text-xs">
                      {c.name.slice(0, 2).toUpperCase()}
                    </div>
                    <div>
                      <div className="font-bold text-sm text-slate-100">{c.name}</div>
                      <div className="text-xs text-slate-400 font-mono flex items-center gap-2 mt-0.5">
                        <span>{c.phone}</span>
                        {c.email && <span>• {c.email}</span>}
                      </div>
                    </div>
                  </div>
                  <ChevronRight className="w-4 h-4 text-slate-500" />
                </div>
              ))}
            </div>
          )}
        </div>

        {/* Customer Profile Side Drawer */}
        <div className="bg-slate-900 border border-slate-800 rounded-2xl p-5">
          <h3 className="font-bold text-sm text-white mb-4 flex items-center gap-2">
            <UserCheck className="w-4 h-4 text-emerald-400" />
            Customer History & Profile
          </h3>

          {!selectedCustomerId ? (
            <div className="py-12 text-center text-xs text-slate-500">
              Select any customer from the list to view their past calls, appointments, and preferences.
            </div>
          ) : loadingDetail ? (
            <div className="py-12 text-center text-xs text-slate-500">Loading details...</div>
          ) : customerDetail ? (
            <div className="space-y-4">
              <div className="p-4 rounded-xl bg-slate-950 border border-slate-800">
                <div className="font-bold text-base text-white">{customerDetail.name}</div>
                <div className="text-xs text-emerald-400 font-mono mt-1">{customerDetail.phone}</div>
                {customerDetail.email && (
                  <div className="text-xs text-slate-400 mt-0.5">{customerDetail.email}</div>
                )}
                {customerDetail.notes && (
                  <p className="text-xs text-slate-300 mt-2 p-2 bg-slate-900 rounded-lg italic">
                    "{customerDetail.notes}"
                  </p>
                )}
              </div>

              {/* Past Appointments */}
              <div>
                <h4 className="text-xs font-semibold text-slate-300 mb-2">Past Appointments ({customerDetail.appointments_count})</h4>
                {customerDetail.recent_appointments.length === 0 ? (
                  <p className="text-[11px] text-slate-500">No appointments scheduled.</p>
                ) : (
                  <div className="space-y-1.5">
                    {customerDetail.recent_appointments.map((a: any) => (
                      <div key={a.id} className="p-2.5 rounded-xl bg-slate-950 border border-slate-800 text-xs">
                        <div className="font-medium text-slate-200">{a.service_name}</div>
                        <div className="text-[11px] text-slate-400 mt-0.5 flex justify-between">
                          <span>{new Date(a.start_time).toLocaleDateString()}</span>
                          <span className="text-emerald-400">{a.status}</span>
                        </div>
                      </div>
                    ))}
                  </div>
                )}
              </div>

              {/* Past Calls */}
              <div>
                <h4 className="text-xs font-semibold text-slate-300 mb-2">Recent Inbound Calls ({customerDetail.calls_count})</h4>
                {customerDetail.recent_calls.length === 0 ? (
                  <p className="text-[11px] text-slate-500">No call records found.</p>
                ) : (
                  <div className="space-y-1.5">
                    {customerDetail.recent_calls.map((c: any) => (
                      <div key={c.id} className="p-2.5 rounded-xl bg-slate-950 border border-slate-800 text-xs">
                        <div className="text-slate-200 flex justify-between">
                          <span>Outcome: {c.outcome}</span>
                          <span className="text-slate-500 font-mono">{c.duration_seconds}s</span>
                        </div>
                      </div>
                    ))}
                  </div>
                )}
              </div>
            </div>
          ) : null}
        </div>
      </div>

      {/* Create Customer Modal */}
      {isCreateOpen && (
        <div className="fixed inset-0 z-50 bg-black/70 backdrop-blur-sm flex items-center justify-center p-4">
          <div className="bg-slate-900 border border-slate-800 rounded-2xl max-w-md w-full p-6 space-y-4">
            <h3 className="font-bold text-base text-white">Add Customer Profile</h3>
            {createError && (
              <div className="p-3 rounded-xl bg-rose-500/10 text-rose-400 text-xs">{createError}</div>
            )}
            <form onSubmit={handleCreateCustomer} className="space-y-3">
              <div>
                <label className="block text-xs font-medium text-slate-300 mb-1">Full Name</label>
                <input
                  type="text"
                  required
                  value={name}
                  onChange={(e) => setName(e.target.value)}
                  placeholder="e.g. Aditi Rao"
                  className="w-full bg-slate-950 border border-slate-800 rounded-xl px-3 py-2 text-xs text-slate-100 focus:outline-none focus:border-emerald-500"
                />
              </div>
              <div>
                <label className="block text-xs font-medium text-slate-300 mb-1">Phone Number (with Country Code)</label>
                <input
                  type="text"
                  required
                  value={phone}
                  onChange={(e) => setPhone(e.target.value)}
                  placeholder="+919876543210"
                  className="w-full bg-slate-950 border border-slate-800 rounded-xl px-3 py-2 text-xs text-slate-100 focus:outline-none focus:border-emerald-500"
                />
              </div>
              <div>
                <label className="block text-xs font-medium text-slate-300 mb-1">Email (Optional)</label>
                <input
                  type="email"
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  placeholder="aditi@example.com"
                  className="w-full bg-slate-950 border border-slate-800 rounded-xl px-3 py-2 text-xs text-slate-100 focus:outline-none focus:border-emerald-500"
                />
              </div>
              <div>
                <label className="block text-xs font-medium text-slate-300 mb-1">Notes / Preferences</label>
                <textarea
                  rows={2}
                  value={notes}
                  onChange={(e) => setNotes(e.target.value)}
                  placeholder="e.g. VIP patient, allergic to penicillin."
                  className="w-full bg-slate-950 border border-slate-800 rounded-xl px-3 py-2 text-xs text-slate-100 focus:outline-none focus:border-emerald-500"
                />
              </div>
              <div className="flex justify-end gap-2 pt-2 border-t border-slate-800">
                <button
                  type="button"
                  onClick={() => setIsCreateOpen(false)}
                  className="px-3 py-1.5 rounded-xl bg-slate-800 text-xs text-slate-300"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  className="px-3 py-1.5 rounded-xl bg-emerald-500 hover:bg-emerald-600 text-slate-950 font-bold text-xs"
                >
                  Save Profile
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
};
