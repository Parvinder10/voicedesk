import React, { useState, useEffect } from 'react';
import { api } from '../services/api';
import { useAuth } from '../contexts/AuthContext';
import { Settings as SettingsIcon, Save, Building2, ShieldAlert, CheckCircle2 } from 'lucide-react';

export const SettingsPage: React.FC = () => {
  const { refreshOrg } = useAuth();
  const [settings, setSettings] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [success, setSuccess] = useState(false);

  // Form Fields
  const [businessName, setBusinessName] = useState('');
  const [industry, setIndustry] = useState('clinic');
  const [address, setAddress] = useState('');
  const [contactEmail, setContactEmail] = useState('');
  const [contactPhone, setContactPhone] = useState('');
  const [duration, setDuration] = useState(30);
  const [buffer, setBuffer] = useState(10);
  const [minNotice, setMinNotice] = useState(2);
  const [maxAdvance, setMaxAdvance] = useState(30);
  const [cancellationPolicy, setCancellationPolicy] = useState('');

  const fetchSettings = async () => {
    try {
      setLoading(true);
      const data = await api.getSettings();
      setSettings(data);
      setBusinessName(data.business_name || '');
      setIndustry(data.industry || 'clinic');
      setAddress(data.address || '');
      setContactEmail(data.contact_email || '');
      setContactPhone(data.contact_phone || '');
      setDuration(data.default_appointment_duration || 30);
      setBuffer(data.buffer_time_minutes || 10);
      setMinNotice(data.min_booking_notice_hours || 2);
      setMaxAdvance(data.max_booking_days_in_advance || 30);
      setCancellationPolicy(data.cancellation_policy || '');
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchSettings();
  }, []);

  const handleSave = async (e: React.FormEvent) => {
    e.preventDefault();
    setSaving(true);
    setSuccess(false);
    try {
      await api.updateSettings({
        business_name: businessName,
        industry,
        address,
        contact_email: contactEmail || null,
        contact_phone: contactPhone || null,
        default_appointment_duration: Number(duration),
        buffer_time_minutes: Number(buffer),
        min_booking_notice_hours: Number(minNotice),
        max_booking_days_in_advance: Number(maxAdvance),
        cancellation_policy: cancellationPolicy
      });
      await refreshOrg();
      setSuccess(true);
      setTimeout(() => setSuccess(false), 3000);
    } catch (err: any) {
      alert(err.message || 'Failed to save settings');
    } finally {
      setSaving(false);
    }
  };

  if (loading) {
    return <div className="p-8 text-center text-xs text-slate-400">Loading settings...</div>;
  }

  return (
    <div className="space-y-6 max-w-4xl">
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-xl font-bold text-white tracking-tight">Business Profile & Booking Policies</h2>
          <p className="text-xs text-slate-400 mt-0.5">
            Configure core business identity, contact channels, buffer times, and appointment cancellation rules.
          </p>
        </div>

        {success && (
          <span className="text-xs text-emerald-400 flex items-center gap-1.5 font-medium">
            <CheckCircle2 className="w-4 h-4" />
            Changes saved successfully!
          </span>
        )}
      </div>

      <form onSubmit={handleSave} className="space-y-6">
        {/* Business Information Card */}
        <div className="p-6 rounded-2xl bg-slate-900 border border-slate-800 space-y-4">
          <h3 className="font-bold text-sm text-white flex items-center gap-2 pb-2 border-b border-slate-800">
            <Building2 className="w-4 h-4 text-emerald-400" />
            Business Details
          </h3>

          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            <div>
              <label className="block text-xs font-medium text-slate-300 mb-1">Business Name</label>
              <input
                type="text"
                required
                value={businessName}
                onChange={(e) => setBusinessName(e.target.value)}
                className="w-full bg-slate-950 border border-slate-800 rounded-xl px-3 py-2 text-xs text-slate-100 focus:outline-none focus:border-emerald-500"
              />
            </div>
            <div>
              <label className="block text-xs font-medium text-slate-300 mb-1">Industry Type</label>
              <select
                value={industry}
                onChange={(e) => setIndustry(e.target.value)}
                className="w-full bg-slate-950 border border-slate-800 rounded-xl px-3 py-2 text-xs text-slate-100 focus:outline-none focus:border-emerald-500"
              >
                <option value="clinic">Clinic & Healthcare</option>
                <option value="salon">Salon & Spa</option>
                <option value="education">Educational Institute</option>
                <option value="real_estate">Real Estate Agency</option>
                <option value="home_service">Home Services / Repair</option>
              </select>
            </div>
          </div>

          <div>
            <label className="block text-xs font-medium text-slate-300 mb-1">Physical Address</label>
            <textarea
              rows={2}
              value={address}
              onChange={(e) => setAddress(e.target.value)}
              placeholder="Suite 402, Pinnacle Plaza, Bandra West..."
              className="w-full bg-slate-950 border border-slate-800 rounded-xl p-3 text-xs text-slate-100 focus:outline-none focus:border-emerald-500"
            />
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            <div>
              <label className="block text-xs font-medium text-slate-300 mb-1">Contact Email</label>
              <input
                type="email"
                value={contactEmail}
                onChange={(e) => setContactEmail(e.target.value)}
                className="w-full bg-slate-950 border border-slate-800 rounded-xl px-3 py-2 text-xs text-slate-100 focus:outline-none focus:border-emerald-500"
              />
            </div>
            <div>
              <label className="block text-xs font-medium text-slate-300 mb-1">Contact Phone</label>
              <input
                type="text"
                value={contactPhone}
                onChange={(e) => setContactPhone(e.target.value)}
                className="w-full bg-slate-950 border border-slate-800 rounded-xl px-3 py-2 text-xs text-slate-100 focus:outline-none focus:border-emerald-500"
              />
            </div>
          </div>
        </div>

        {/* Appointment Rules Card */}
        <div className="p-6 rounded-2xl bg-slate-900 border border-slate-800 space-y-4">
          <h3 className="font-bold text-sm text-white flex items-center gap-2 pb-2 border-b border-slate-800">
            <ShieldAlert className="w-4 h-4 text-emerald-400" />
            Scheduling & Policy Rules
          </h3>

          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
            <div>
              <label className="block text-xs font-medium text-slate-300 mb-1">Default Duration</label>
              <div className="flex items-center gap-1.5">
                <input
                  type="number"
                  min={10}
                  max={240}
                  step={5}
                  value={duration}
                  onChange={(e) => setDuration(Number(e.target.value))}
                  className="w-full bg-slate-950 border border-slate-800 rounded-xl px-3 py-2 text-xs text-slate-100 focus:outline-none focus:border-emerald-500"
                />
                <span className="text-xs text-slate-400">mins</span>
              </div>
            </div>

            <div>
              <label className="block text-xs font-medium text-slate-300 mb-1">Buffer Time</label>
              <div className="flex items-center gap-1.5">
                <input
                  type="number"
                  min={0}
                  max={60}
                  step={5}
                  value={buffer}
                  onChange={(e) => setBuffer(Number(e.target.value))}
                  className="w-full bg-slate-950 border border-slate-800 rounded-xl px-3 py-2 text-xs text-slate-100 focus:outline-none focus:border-emerald-500"
                />
                <span className="text-xs text-slate-400">mins</span>
              </div>
            </div>

            <div>
              <label className="block text-xs font-medium text-slate-300 mb-1">Min Booking Notice</label>
              <div className="flex items-center gap-1.5">
                <input
                  type="number"
                  min={0}
                  max={48}
                  value={minNotice}
                  onChange={(e) => setMinNotice(Number(e.target.value))}
                  className="w-full bg-slate-950 border border-slate-800 rounded-xl px-3 py-2 text-xs text-slate-100 focus:outline-none focus:border-emerald-500"
                />
                <span className="text-xs text-slate-400">hrs</span>
              </div>
            </div>

            <div>
              <label className="block text-xs font-medium text-slate-300 mb-1">Max Advance Booking</label>
              <div className="flex items-center gap-1.5">
                <input
                  type="number"
                  min={1}
                  max={180}
                  value={maxAdvance}
                  onChange={(e) => setMaxAdvance(Number(e.target.value))}
                  className="w-full bg-slate-950 border border-slate-800 rounded-xl px-3 py-2 text-xs text-slate-100 focus:outline-none focus:border-emerald-500"
                />
                <span className="text-xs text-slate-400">days</span>
              </div>
            </div>
          </div>

          <div>
            <label className="block text-xs font-medium text-slate-300 mb-1">Cancellation Policy Disclosure</label>
            <textarea
              rows={2}
              value={cancellationPolicy}
              onChange={(e) => setCancellationPolicy(e.target.value)}
              placeholder="e.g. Appointments can be rescheduled or cancelled with at least 4 hours advance notice."
              className="w-full bg-slate-950 border border-slate-800 rounded-xl p-3 text-xs text-slate-100 focus:outline-none focus:border-emerald-500"
            />
          </div>
        </div>

        <div className="flex justify-end">
          <button
            type="submit"
            disabled={saving}
            className="px-6 py-2.5 rounded-xl bg-emerald-500 hover:bg-emerald-600 disabled:opacity-50 text-slate-950 font-bold text-xs flex items-center gap-2 shadow-lg shadow-emerald-500/10"
          >
            <Save className="w-4 h-4" />
            {saving ? 'Saving...' : 'Save Configuration'}
          </button>
        </div>
      </form>
    </div>
  );
};
