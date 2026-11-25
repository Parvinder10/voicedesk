import React, { useState, useEffect } from 'react';
import { api } from '../services/api';
import { Clock, Calendar, Save, Plus, Trash2, CheckCircle2, AlertCircle } from 'lucide-react';

const DAYS = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday'];

export const AvailabilityPage: React.FC = () => {
  const [hours, setHours] = useState<any[]>([]);
  const [holidays, setHolidays] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [saveSuccess, setSaveSuccess] = useState(false);

  // New Holiday
  const [holidayName, setHolidayName] = useState('');
  const [holidayDate, setHolidayDate] = useState('');
  const [holidayError, setHolidayError] = useState<string | null>(null);

  const fetchAvailability = async () => {
    try {
      setLoading(true);
      const [hoursData, holidaysData] = await Promise.all([
        api.getHours(),
        api.getHolidays()
      ]);
      setHours(hoursData);
      setHolidays(holidaysData);
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchAvailability();
  }, []);

  const handleHourChange = (dayIndex: number, field: string, value: any) => {
    setHours((prev) =>
      prev.map((h) => (h.day_of_week === dayIndex ? { ...h, [field]: value } : h))
    );
  };

  const handleSaveHours = async () => {
    setSaving(true);
    setSaveSuccess(false);
    try {
      const payload = hours.map((h) => ({
        day_of_week: h.day_of_week,
        open_time: h.open_time,
        close_time: h.close_time,
        is_closed: h.is_closed
      }));
      await api.updateHours(payload);
      setSaveSuccess(true);
      setTimeout(() => setSaveSuccess(false), 3000);
    } catch (err: any) {
      alert(err.message || 'Failed to update operating hours');
    } finally {
      setSaving(false);
    }
  };

  const handleAddHoliday = async (e: React.FormEvent) => {
    e.preventDefault();
    setHolidayError(null);
    try {
      await api.addHoliday({ name: holidayName, date: holidayDate });
      setHolidayName('');
      setHolidayDate('');
      fetchAvailability();
    } catch (err: any) {
      setHolidayError(err.message || 'Failed to add holiday');
    }
  };

  const handleDeleteHoliday = async (id: string) => {
    try {
      await api.deleteHoliday(id);
      fetchAvailability();
    } catch (err: any) {
      alert(err.message || 'Failed to delete holiday');
    }
  };

  return (
    <div className="space-y-6">
      <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
        <div>
          <h2 className="text-xl font-bold text-white tracking-tight">Availability & Business Hours</h2>
          <p className="text-xs text-slate-400 mt-0.5">
            Configure weekly operating schedules and scheduled business closures that govern AI booking availability.
          </p>
        </div>

        <button
          onClick={handleSaveHours}
          disabled={saving}
          className="px-4 py-2 rounded-xl bg-emerald-500 hover:bg-emerald-600 disabled:opacity-50 text-slate-950 font-bold text-xs transition-colors flex items-center gap-1.5 shadow-lg shadow-emerald-500/10"
        >
          <Save className="w-4 h-4" />
          {saving ? 'Saving...' : saveSuccess ? 'Saved Successfully!' : 'Save Weekly Schedule'}
        </button>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Weekly Hours Table */}
        <div className="lg:col-span-2 bg-slate-900 border border-slate-800 rounded-2xl p-6 space-y-4">
          <div className="flex items-center justify-between pb-3 border-b border-slate-800">
            <h3 className="font-bold text-sm text-white flex items-center gap-2">
              <Clock className="w-4 h-4 text-emerald-400" />
              Weekly Operating Schedule
            </h3>
            <span className="text-xs text-slate-400">24-hour HH:MM format</span>
          </div>

          {loading ? (
            <div className="p-8 text-center text-xs text-slate-400">Loading hours...</div>
          ) : (
            <div className="divide-y divide-slate-800/80">
              {hours.map((h) => (
                <div key={h.day_of_week} className="py-3.5 flex items-center justify-between gap-4 text-xs">
                  <div className="w-28 font-semibold text-slate-200">
                    {DAYS[h.day_of_week]}
                  </div>

                  <div className="flex items-center gap-3">
                    <label className="flex items-center gap-1.5 cursor-pointer text-slate-400">
                      <input
                        type="checkbox"
                        checked={h.is_closed}
                        onChange={(e) => handleHourChange(h.day_of_week, 'is_closed', e.target.checked)}
                        className="rounded border-slate-700 bg-slate-950 text-emerald-500 focus:ring-0"
                      />
                      <span>Closed</span>
                    </label>

                    {!h.is_closed && (
                      <div className="flex items-center gap-2">
                        <input
                          type="time"
                          value={h.open_time}
                          onChange={(e) => handleHourChange(h.day_of_week, 'open_time', e.target.value)}
                          className="bg-slate-950 border border-slate-800 rounded-lg px-2 py-1 text-slate-200 focus:outline-none focus:border-emerald-500"
                        />
                        <span className="text-slate-500">to</span>
                        <input
                          type="time"
                          value={h.close_time}
                          onChange={(e) => handleHourChange(h.day_of_week, 'close_time', e.target.value)}
                          className="bg-slate-950 border border-slate-800 rounded-lg px-2 py-1 text-slate-200 focus:outline-none focus:border-emerald-500"
                        />
                      </div>
                    )}
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>

        {/* Holidays & Closures Side Panel */}
        <div className="bg-slate-900 border border-slate-800 rounded-2xl p-6 space-y-5">
          <h3 className="font-bold text-sm text-white flex items-center gap-2">
            <Calendar className="w-4 h-4 text-emerald-400" />
            Holidays & Closures
          </h3>

          <form onSubmit={handleAddHoliday} className="space-y-3">
            {holidayError && (
              <div className="p-2.5 rounded-xl bg-rose-500/10 text-rose-400 text-xs">{holidayError}</div>
            )}
            <div>
              <label className="block text-xs font-medium text-slate-300 mb-1">Holiday / Closure Name</label>
              <input
                type="text"
                required
                value={holidayName}
                onChange={(e) => setHolidayName(e.target.value)}
                placeholder="e.g. Diwali Festival"
                className="w-full bg-slate-950 border border-slate-800 rounded-xl px-3 py-2 text-xs text-slate-100 focus:outline-none focus:border-emerald-500"
              />
            </div>
            <div>
              <label className="block text-xs font-medium text-slate-300 mb-1">Date</label>
              <input
                type="date"
                required
                value={holidayDate}
                onChange={(e) => setHolidayDate(e.target.value)}
                className="w-full bg-slate-950 border border-slate-800 rounded-xl px-3 py-2 text-xs text-slate-100 focus:outline-none focus:border-emerald-500"
              />
            </div>
            <button
              type="submit"
              className="w-full py-2 px-3 rounded-xl bg-slate-800 hover:bg-slate-700 text-slate-200 font-semibold text-xs transition-colors flex items-center justify-center gap-1.5"
            >
              <Plus className="w-3.5 h-3.5" />
              Add Scheduled Closure
            </button>
          </form>

          {/* Scheduled Holidays List */}
          <div className="pt-2 border-t border-slate-800 space-y-2 max-h-56 overflow-y-auto">
            {holidays.length === 0 ? (
              <p className="text-xs text-slate-500 text-center py-4">No scheduled closures found.</p>
            ) : (
              holidays.map((h) => (
                <div key={h.id} className="p-2.5 rounded-xl bg-slate-950 border border-slate-850 flex items-center justify-between text-xs">
                  <div>
                    <div className="font-medium text-slate-200">{h.name}</div>
                    <div className="text-[11px] text-slate-500 font-mono">{h.date}</div>
                  </div>
                  <button
                    onClick={() => handleDeleteHoliday(h.id)}
                    className="p-1 text-slate-500 hover:text-rose-400"
                  >
                    <Trash2 className="w-3.5 h-3.5" />
                  </button>
                </div>
              ))
            )}
          </div>
        </div>
      </div>
    </div>
  );
};
