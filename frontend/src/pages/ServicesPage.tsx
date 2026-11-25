import React, { useState, useEffect } from 'react';
import { api } from '../services/api';
import { Briefcase, Plus, Clock, Tag, Trash2, Edit2, CheckCircle2, AlertCircle } from 'lucide-react';

export const ServicesPage: React.FC = () => {
  const [services, setServices] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [editingService, setEditingService] = useState<any>(null);

  const [name, setName] = useState('');
  const [description, setDescription] = useState('');
  const [durationMinutes, setDurationMinutes] = useState(30);
  const [price, setPrice] = useState(500);
  const [currency, setCurrency] = useState('INR');
  const [error, setError] = useState<string | null>(null);

  const fetchServices = async () => {
    try {
      setLoading(true);
      const data = await api.getServices();
      setServices(data);
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchServices();
  }, []);

  const openCreateModal = () => {
    setEditingService(null);
    setName('');
    setDescription('');
    setDurationMinutes(30);
    setPrice(500);
    setCurrency('INR');
    setError(null);
    setIsModalOpen(true);
  };

  const openEditModal = (s: any) => {
    setEditingService(s);
    setName(s.name);
    setDescription(s.description || '');
    setDurationMinutes(s.duration_minutes);
    setPrice(s.price);
    setCurrency(s.currency);
    setError(null);
    setIsModalOpen(true);
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);
    try {
      if (editingService) {
        await api.updateService(editingService.id, {
          name,
          description,
          duration_minutes: Number(durationMinutes),
          price: Number(price),
          currency
        });
      } else {
        await api.createService({
          name,
          description,
          duration_minutes: Number(durationMinutes),
          price: Number(price),
          currency
        });
      }
      setIsModalOpen(false);
      fetchServices();
    } catch (err: any) {
      setError(err.message || 'Operation failed');
    }
  };

  const handleDelete = async (id: string) => {
    if (confirm('Are you sure you want to deactivate this service?')) {
      try {
        await api.deleteService(id);
        fetchServices();
      } catch (err: any) {
        alert(err.message || 'Failed to delete service');
      }
    }
  };

  return (
    <div className="space-y-6">
      <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
        <div>
          <h2 className="text-xl font-bold text-white tracking-tight">Services & Pricing Menu</h2>
          <p className="text-xs text-slate-400 mt-0.5">
            Configure services, duration, and pricing that the Voice Receptionist uses to quote callers and book time slots.
          </p>
        </div>

        <button
          onClick={openCreateModal}
          className="px-4 py-2 rounded-xl bg-emerald-500 hover:bg-emerald-600 text-slate-950 font-semibold text-xs transition-colors flex items-center gap-1.5 shadow-lg shadow-emerald-500/10"
        >
          <Plus className="w-4 h-4" />
          Add Service
        </button>
      </div>

      {/* Services Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        {loading ? (
          <div className="col-span-full p-8 text-center text-xs text-slate-400">Loading services...</div>
        ) : services.length === 0 ? (
          <div className="col-span-full p-12 text-center text-slate-500 text-xs">
            <Briefcase className="w-8 h-8 mx-auto mb-2 text-slate-600" />
            No services configured. Add your first service to enable appointment booking.
          </div>
        ) : (
          services.map((s) => (
            <div
              key={s.id}
              className="p-5 rounded-2xl bg-slate-900 border border-slate-800 flex flex-col justify-between hover:border-slate-700 transition-colors"
            >
              <div>
                <div className="flex items-start justify-between gap-2">
                  <h3 className="font-bold text-sm text-white">{s.name}</h3>
                  <span className="text-xs font-mono font-bold text-emerald-400 bg-emerald-500/10 px-2 py-0.5 rounded-full border border-emerald-500/20">
                    {s.currency} {s.price}
                  </span>
                </div>

                <p className="text-xs text-slate-400 mt-2 line-clamp-2">
                  {s.description || 'No description provided.'}
                </p>
              </div>

              <div className="pt-4 mt-4 border-t border-slate-800/80 flex items-center justify-between">
                <span className="text-xs text-slate-400 flex items-center gap-1 font-mono">
                  <Clock className="w-3.5 h-3.5 text-slate-500" />
                  {s.duration_minutes} mins
                </span>

                <div className="flex items-center gap-1">
                  <button
                    onClick={() => openEditModal(s)}
                    className="p-1.5 text-slate-400 hover:text-white rounded-lg hover:bg-slate-800"
                  >
                    <Edit2 className="w-3.5 h-3.5" />
                  </button>
                  <button
                    onClick={() => handleDelete(s.id)}
                    className="p-1.5 text-slate-400 hover:text-rose-400 rounded-lg hover:bg-rose-500/10"
                  >
                    <Trash2 className="w-3.5 h-3.5" />
                  </button>
                </div>
              </div>
            </div>
          ))
        )}
      </div>

      {/* Add / Edit Service Modal */}
      {isModalOpen && (
        <div className="fixed inset-0 z-50 bg-black/70 backdrop-blur-sm flex items-center justify-center p-4">
          <div className="bg-slate-900 border border-slate-800 rounded-2xl max-w-md w-full p-6 space-y-4">
            <h3 className="font-bold text-base text-white">
              {editingService ? 'Edit Service' : 'Add New Service'}
            </h3>

            {error && (
              <div className="p-3 rounded-xl bg-rose-500/10 text-rose-400 text-xs">{error}</div>
            )}

            <form onSubmit={handleSubmit} className="space-y-3">
              <div>
                <label className="block text-xs font-medium text-slate-300 mb-1">Service Name</label>
                <input
                  type="text"
                  required
                  value={name}
                  onChange={(e) => setName(e.target.value)}
                  placeholder="e.g. Teeth Whitening"
                  className="w-full bg-slate-950 border border-slate-800 rounded-xl px-3 py-2 text-xs text-slate-100 focus:outline-none focus:border-emerald-500"
                />
              </div>

              <div>
                <label className="block text-xs font-medium text-slate-300 mb-1">Description</label>
                <textarea
                  rows={2}
                  value={description}
                  onChange={(e) => setDescription(e.target.value)}
                  placeholder="Detailed description of the procedure or treatment."
                  className="w-full bg-slate-950 border border-slate-800 rounded-xl px-3 py-2 text-xs text-slate-100 focus:outline-none focus:border-emerald-500"
                />
              </div>

              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block text-xs font-medium text-slate-300 mb-1">Duration (Minutes)</label>
                  <input
                    type="number"
                    min={5}
                    max={480}
                    step={5}
                    value={durationMinutes}
                    onChange={(e) => setDurationMinutes(Number(e.target.value))}
                    className="w-full bg-slate-950 border border-slate-800 rounded-xl px-3 py-2 text-xs text-slate-100 focus:outline-none focus:border-emerald-500"
                  />
                </div>
                <div>
                  <label className="block text-xs font-medium text-slate-300 mb-1">Price (₹)</label>
                  <input
                    type="number"
                    min={0}
                    step={50}
                    value={price}
                    onChange={(e) => setPrice(Number(e.target.value))}
                    className="w-full bg-slate-950 border border-slate-800 rounded-xl px-3 py-2 text-xs text-slate-100 focus:outline-none focus:border-emerald-500"
                  />
                </div>
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
                  Save Service
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
};
