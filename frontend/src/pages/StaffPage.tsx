import React, { useState, useEffect } from 'react';
import { api } from '../services/api';
import { UserCheck, Plus, Mail, Phone, Trash2, Edit2, User } from 'lucide-react';

export const StaffPage: React.FC = () => {
  const [staff, setStaff] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [name, setName] = useState('');
  const [title, setTitle] = useState('');
  const [email, setEmail] = useState('');
  const [phone, setPhone] = useState('');
  const [error, setError] = useState<string | null>(null);

  const fetchStaff = async () => {
    try {
      setLoading(true);
      const data = await api.getStaff();
      setStaff(data);
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchStaff();
  }, []);

  const handleCreate = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);
    try {
      await api.createStaff({ name, title, email: email || null, phone: phone || null });
      setIsModalOpen(false);
      setName('');
      setTitle('');
      setEmail('');
      setPhone('');
      fetchStaff();
    } catch (err: any) {
      setError(err.message || 'Failed to add staff');
    }
  };

  const handleDelete = async (id: string) => {
    if (confirm('Are you sure you want to remove this staff member?')) {
      try {
        await api.deleteStaff(id);
        fetchStaff();
      } catch (err: any) {
        alert(err.message || 'Failed to remove staff');
      }
    }
  };

  return (
    <div className="space-y-6">
      <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
        <div>
          <h2 className="text-xl font-bold text-white tracking-tight">Staff & Practitioners</h2>
          <p className="text-xs text-slate-400 mt-0.5">
            Manage practitioners, specialists, and team members whose schedules dictate real appointment availability.
          </p>
        </div>

        <button
          onClick={() => { setError(null); setIsModalOpen(true); }}
          className="px-4 py-2 rounded-xl bg-emerald-500 hover:bg-emerald-600 text-slate-950 font-semibold text-xs transition-colors flex items-center gap-1.5 shadow-lg shadow-emerald-500/10"
        >
          <Plus className="w-4 h-4" />
          Add Staff Member
        </button>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        {loading ? (
          <div className="col-span-full p-8 text-center text-xs text-slate-400">Loading staff roster...</div>
        ) : staff.length === 0 ? (
          <div className="col-span-full p-12 text-center text-slate-500 text-xs">
            <UserCheck className="w-8 h-8 mx-auto mb-2 text-slate-600" />
            No staff members found. Add your practitioners to calculate availability slots.
          </div>
        ) : (
          staff.map((st) => (
            <div
              key={st.id}
              className="p-5 rounded-2xl bg-slate-900 border border-slate-800 flex items-start justify-between hover:border-slate-700 transition-colors"
            >
              <div className="flex items-start gap-3">
                <div className="w-10 h-10 rounded-full bg-emerald-500/10 text-emerald-400 border border-emerald-500/20 flex items-center justify-center font-bold text-sm">
                  {st.name.slice(0, 2).toUpperCase()}
                </div>
                <div>
                  <h3 className="font-bold text-sm text-white">{st.name}</h3>
                  <div className="text-xs text-emerald-400 font-medium mt-0.5">{st.title || 'Staff Member'}</div>
                  <div className="space-y-0.5 mt-2 text-[11px] text-slate-400 font-mono">
                    {st.email && (
                      <div className="flex items-center gap-1.5">
                        <Mail className="w-3 h-3 text-slate-500" />
                        <span>{st.email}</span>
                      </div>
                    )}
                    {st.phone && (
                      <div className="flex items-center gap-1.5">
                        <Phone className="w-3 h-3 text-slate-500" />
                        <span>{st.phone}</span>
                      </div>
                    )}
                  </div>
                </div>
              </div>

              <button
                onClick={() => handleDelete(st.id)}
                className="p-1.5 text-slate-500 hover:text-rose-400 rounded-lg hover:bg-rose-500/10"
              >
                <Trash2 className="w-3.5 h-3.5" />
              </button>
            </div>
          ))
        )}
      </div>

      {isModalOpen && (
        <div className="fixed inset-0 z-50 bg-black/70 backdrop-blur-sm flex items-center justify-center p-4">
          <div className="bg-slate-900 border border-slate-800 rounded-2xl max-w-md w-full p-6 space-y-4">
            <h3 className="font-bold text-base text-white">Add Staff Member</h3>
            {error && (
              <div className="p-3 rounded-xl bg-rose-500/10 text-rose-400 text-xs">{error}</div>
            )}
            <form onSubmit={handleCreate} className="space-y-3">
              <div>
                <label className="block text-xs font-medium text-slate-300 mb-1">Staff Name</label>
                <input
                  type="text"
                  required
                  value={name}
                  onChange={(e) => setName(e.target.value)}
                  placeholder="e.g. Dr. Kavita Nair"
                  className="w-full bg-slate-950 border border-slate-800 rounded-xl px-3 py-2 text-xs text-slate-100 focus:outline-none focus:border-emerald-500"
                />
              </div>
              <div>
                <label className="block text-xs font-medium text-slate-300 mb-1">Title / Designation</label>
                <input
                  type="text"
                  value={title}
                  onChange={(e) => setTitle(e.target.value)}
                  placeholder="e.g. Senior Periodontist"
                  className="w-full bg-slate-950 border border-slate-800 rounded-xl px-3 py-2 text-xs text-slate-100 focus:outline-none focus:border-emerald-500"
                />
              </div>
              <div>
                <label className="block text-xs font-medium text-slate-300 mb-1">Email (Optional)</label>
                <input
                  type="email"
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  placeholder="kavita@clinic.com"
                  className="w-full bg-slate-950 border border-slate-800 rounded-xl px-3 py-2 text-xs text-slate-100 focus:outline-none focus:border-emerald-500"
                />
              </div>
              <div>
                <label className="block text-xs font-medium text-slate-300 mb-1">Phone (Optional)</label>
                <input
                  type="text"
                  value={phone}
                  onChange={(e) => setPhone(e.target.value)}
                  placeholder="+919876543210"
                  className="w-full bg-slate-950 border border-slate-800 rounded-xl px-3 py-2 text-xs text-slate-100 focus:outline-none focus:border-emerald-500"
                />
              </div>
              <div className="flex justify-end gap-2 pt-2 border-t border-slate-800">
                <button
                  type="button"
                  onClick={() => setIsModalOpen(false)}
                  className="px-3 py-1.5 rounded-xl bg-slate-800 text-xs text-slate-300"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  className="px-4 py-1.5 rounded-xl bg-emerald-500 hover:bg-emerald-600 text-slate-950 font-bold text-xs"
                >
                  Add Staff
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
};
