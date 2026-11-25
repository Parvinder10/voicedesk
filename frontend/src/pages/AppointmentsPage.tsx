import React, { useState, useEffect } from 'react';
import { api } from '../services/api';
import {
  Calendar as CalendarIcon,
  Plus,
  ChevronLeft,
  ChevronRight,
  Clock,
  User,
  CheckCircle2,
  XCircle,
  AlertCircle,
  Filter,
  RefreshCw,
  Search
} from 'lucide-react';

export const AppointmentsPage: React.FC = () => {
  const [appointments, setAppointments] = useState<any[]>([]);
  const [services, setServices] = useState<any[]>([]);
  const [staffList, setStaffList] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [viewMode, setViewMode] = useState<'day' | 'week' | 'month'>('week');
  const [currentDate, setCurrentDate] = useState<Date>(new Date());
  const [statusFilter, setStatusFilter] = useState<string>('');

  // Booking Modal State
  const [isBookModalOpen, setIsBookModalOpen] = useState(false);
  const [selectedServiceId, setSelectedServiceId] = useState('');
  const [bookDate, setBookDate] = useState(new Date().toISOString().split('T')[0]);
  const [availableSlots, setAvailableSlots] = useState<any[]>([]);
  const [loadingSlots, setLoadingSlots] = useState(false);
  const [selectedSlot, setSelectedSlot] = useState<any>(null);
  const [customerName, setCustomerName] = useState('');
  const [customerPhone, setCustomerPhone] = useState('');
  const [notes, setNotes] = useState('');
  const [bookError, setBookError] = useState<string | null>(null);

  // Reschedule Modal State
  const [rescheduleAppt, setRescheduleAppt] = useState<any>(null);
  const [rescheduleDate, setRescheduleDate] = useState('');
  const [rescheduleSlots, setRescheduleSlots] = useState<any[]>([]);
  const [selectedReschedSlot, setSelectedReschedSlot] = useState<any>(null);
  const [rescheduleReason, setRescheduleReason] = useState('');

  // Cancel Modal State
  const [cancelAppt, setCancelAppt] = useState<any>(null);
  const [cancelReason, setCancelReason] = useState('Customer requested cancellation');

  const fetchAppointments = async () => {
    try {
      setLoading(true);
      const [apptsData, servicesData, staffData] = await Promise.all([
        api.getAppointments({ status: statusFilter || undefined }),
        api.getServices(),
        api.getStaff()
      ]);
      setAppointments(apptsData);
      setServices(servicesData);
      setStaffList(staffData);
      if (servicesData.length > 0 && !selectedServiceId) {
        setSelectedServiceId(servicesData[0].id);
      }
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchAppointments();
  }, [statusFilter]);

  // Load real available slots when service or date changes in booking modal
  useEffect(() => {
    if (isBookModalOpen && selectedServiceId && bookDate) {
      fetchAvailableSlots(selectedServiceId, bookDate);
    }
  }, [isBookModalOpen, selectedServiceId, bookDate]);

  const fetchAvailableSlots = async (serviceId: string, dateStr: string) => {
    try {
      setLoadingSlots(true);
      setSelectedSlot(null);
      const res = await api.getAvailability(serviceId, dateStr);
      setAvailableSlots(res.available_slots || []);
    } catch (err: any) {
      setAvailableSlots([]);
    } finally {
      setLoadingSlots(false);
    }
  };

  const handleBookSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!selectedSlot) {
      setBookError('Please select an available time slot.');
      return;
    }
    setBookError(null);
    try {
      await api.bookAppointment({
        service_id: selectedServiceId,
        customer_phone: customerPhone,
        customer_name: customerName,
        staff_id: selectedSlot.available_staff_id,
        start_time: selectedSlot.start_time,
        notes
      });
      setIsBookModalOpen(false);
      setCustomerName('');
      setCustomerPhone('');
      setNotes('');
      fetchAppointments();
    } catch (err: any) {
      setBookError(err.message || 'Double booking prevented or slot unavailable.');
    }
  };

  const handleRescheduleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!selectedReschedSlot) return;
    try {
      await api.rescheduleAppointment(rescheduleAppt.id, {
        new_start_time: selectedReschedSlot.start_time,
        reason: rescheduleReason
      });
      setRescheduleAppt(null);
      fetchAppointments();
    } catch (err: any) {
      alert(err.message || 'Failed to reschedule');
    }
  };

  const handleCancelSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      await api.cancelAppointment(cancelAppt.id, { reason: cancelReason });
      setCancelAppt(null);
      fetchAppointments();
    } catch (err: any) {
      alert(err.message || 'Failed to cancel');
    }
  };

  const navigateDate = (dir: 'prev' | 'next') => {
    const delta = dir === 'prev' ? -1 : 1;
    const newD = new Date(currentDate);
    if (viewMode === 'day') newD.setDate(newD.getDate() + delta);
    else if (viewMode === 'week') newD.setDate(newD.getDate() + delta * 7);
    else if (viewMode === 'month') newD.setMonth(newD.getMonth() + delta);
    setCurrentDate(newD);
  };

  return (
    <div className="space-y-6">
      {/* Top Header */}
      <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
        <div>
          <h2 className="text-xl font-bold text-white tracking-tight">Appointment Scheduling</h2>
          <p className="text-xs text-slate-400 mt-0.5">
            Concurrency-safe booking calendar with automatic conflict detection and timezone support.
          </p>
        </div>

        <div className="flex items-center gap-3">
          {/* View Mode Buttons */}
          <div className="flex rounded-xl bg-slate-900 border border-slate-800 p-1">
            {(['day', 'week', 'month'] as const).map((m) => (
              <button
                key={m}
                onClick={() => setViewMode(m)}
                className={`px-3 py-1.5 rounded-lg text-xs font-semibold capitalize transition-all ${
                  viewMode === m
                    ? 'bg-emerald-500 text-slate-950 shadow-sm'
                    : 'text-slate-400 hover:text-slate-200'
                }`}
              >
                {m}
              </button>
            ))}
          </div>

          <button
            onClick={() => setIsBookModalOpen(true)}
            className="px-4 py-2 rounded-xl bg-emerald-500 hover:bg-emerald-600 text-slate-950 font-semibold text-xs transition-colors flex items-center gap-1.5 shadow-lg shadow-emerald-500/10"
          >
            <Plus className="w-4 h-4" />
            New Booking
          </button>
        </div>
      </div>

      {/* Date Navigation Bar & Filter */}
      <div className="p-4 rounded-2xl bg-slate-900 border border-slate-800 flex flex-wrap items-center justify-between gap-4">
        <div className="flex items-center gap-2">
          <button
            onClick={() => navigateDate('prev')}
            className="p-2 rounded-xl bg-slate-800 hover:bg-slate-700 text-slate-300"
          >
            <ChevronLeft className="w-4 h-4" />
          </button>
          <button
            onClick={() => setCurrentDate(new Date())}
            className="px-3 py-1.5 rounded-xl bg-slate-800 hover:bg-slate-700 text-xs font-medium text-slate-300"
          >
            Today
          </button>
          <button
            onClick={() => navigateDate('next')}
            className="p-2 rounded-xl bg-slate-800 hover:bg-slate-700 text-slate-300"
          >
            <ChevronRight className="w-4 h-4" />
          </button>

          <span className="font-semibold text-sm text-slate-100 ml-2">
            {currentDate.toLocaleDateString('en-US', { month: 'long', year: 'numeric', day: viewMode === 'day' ? 'numeric' : undefined })}
          </span>
        </div>

        <div className="flex items-center gap-2">
          <Filter className="w-3.5 h-3.5 text-slate-400" />
          <select
            value={statusFilter}
            onChange={(e) => setStatusFilter(e.target.value)}
            className="bg-slate-950 border border-slate-800 rounded-xl px-3 py-1.5 text-xs text-slate-300 focus:outline-none"
          >
            <option value="">All Statuses</option>
            <option value="Confirmed">Confirmed</option>
            <option value="Rescheduled">Rescheduled</option>
            <option value="Cancelled">Cancelled</option>
            <option value="Completed">Completed</option>
          </select>
        </div>
      </div>

      {/* Appointments List / Grid */}
      <div className="bg-slate-900 border border-slate-800 rounded-2xl overflow-hidden">
        {loading ? (
          <div className="p-8 text-center text-xs text-slate-400">Loading appointments...</div>
        ) : appointments.length === 0 ? (
          <div className="p-12 text-center text-slate-500 text-xs">
            <CalendarIcon className="w-8 h-8 mx-auto mb-2 text-slate-600" />
            No appointments booked yet. Click "New Booking" to schedule or test via the Voice Agent.
          </div>
        ) : (
          <div className="divide-y divide-slate-800/80">
            {appointments.map((appt) => {
              const startDt = new Date(appt.start_time);
              const isPast = startDt < new Date();
              return (
                <div key={appt.id} className="p-4 sm:p-5 flex flex-col md:flex-row items-start md:items-center justify-between gap-4 hover:bg-slate-850/50 transition-colors">
                  <div className="flex items-start gap-4">
                    <div className="p-3 rounded-2xl bg-slate-800 border border-slate-700/60 text-center min-w-[70px]">
                      <div className="text-[10px] font-bold uppercase text-slate-400">
                        {startDt.toLocaleDateString('en-US', { weekday: 'short' })}
                      </div>
                      <div className="text-lg font-extrabold text-white">
                        {startDt.getDate()}
                      </div>
                      <div className="text-[10px] text-emerald-400 font-mono">
                        {startDt.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
                      </div>
                    </div>

                    <div>
                      <div className="flex items-center gap-2">
                        <span className="font-bold text-sm text-slate-100">{appt.customer_name || 'Guest Customer'}</span>
                        <span className="text-xs text-slate-400 font-mono">({appt.customer_phone})</span>
                        <span className={`text-[10px] font-semibold px-2 py-0.5 rounded-full border ${
                          appt.status === 'Confirmed' ? 'bg-emerald-500/10 text-emerald-400 border-emerald-500/20' :
                          appt.status === 'Rescheduled' ? 'bg-amber-500/10 text-amber-400 border-amber-500/20' :
                          appt.status === 'Cancelled' ? 'bg-rose-500/10 text-rose-400 border-rose-500/20' :
                          'bg-blue-500/10 text-blue-400 border-blue-500/20'
                        }`}>
                          {appt.status}
                        </span>
                      </div>

                      <div className="text-xs text-slate-300 mt-1 flex items-center gap-3">
                        <span className="text-emerald-400 font-medium">{appt.service_name}</span>
                        {appt.staff_name && (
                          <span className="text-slate-400 flex items-center gap-1">
                            <User className="w-3 h-3 text-slate-500" />
                            {appt.staff_name}
                          </span>
                        )}
                        {appt.service_price && (
                          <span className="text-slate-400 font-mono">₹{appt.service_price}</span>
                        )}
                      </div>

                      {appt.notes && (
                        <p className="text-[11px] text-slate-400 mt-1 italic">
                          "{appt.notes}"
                        </p>
                      )}
                      {appt.cancellation_reason && (
                        <p className="text-[11px] text-rose-400 mt-1">
                          Cancellation Reason: {appt.cancellation_reason}
                        </p>
                      )}
                    </div>
                  </div>

                  {/* Actions */}
                  {appt.status !== 'Cancelled' && (
                    <div className="flex items-center gap-2 self-end md:self-auto">
                      <button
                        onClick={() => {
                          setRescheduleAppt(appt);
                          setRescheduleDate(appt.start_time.split('T')[0]);
                          fetchAvailableSlots(appt.service_id, appt.start_time.split('T')[0]).then((res: any) => {
                            // sets slots
                          });
                        }}
                        className="px-3 py-1.5 rounded-xl bg-slate-800 hover:bg-slate-700 text-xs font-medium text-slate-300 transition-colors"
                      >
                        Reschedule
                      </button>
                      <button
                        onClick={() => setCancelAppt(appt)}
                        className="px-3 py-1.5 rounded-xl bg-rose-500/10 hover:bg-rose-500/20 text-xs font-medium text-rose-400 border border-rose-500/20 transition-colors"
                      >
                        Cancel
                      </button>
                    </div>
                  )}
                </div>
              );
            })}
          </div>
        )}
      </div>

      {/* Book New Appointment Modal */}
      {isBookModalOpen && (
        <div className="fixed inset-0 z-50 bg-black/70 backdrop-blur-sm flex items-center justify-center p-4">
          <div className="bg-slate-900 border border-slate-800 rounded-2xl max-w-lg w-full p-6 space-y-4 max-h-[90vh] overflow-y-auto">
            <div className="flex items-center justify-between pb-3 border-b border-slate-800">
              <h3 className="font-bold text-base text-white">Book Confirmed Appointment</h3>
              <button onClick={() => setIsBookModalOpen(false)} className="text-slate-400 hover:text-white">✕</button>
            </div>

            {bookError && (
              <div className="p-3 rounded-xl bg-rose-500/10 border border-rose-500/20 text-rose-400 text-xs flex items-center gap-2">
                <AlertCircle className="w-4 h-4 shrink-0" />
                <span>{bookError}</span>
              </div>
            )}

            <form onSubmit={handleBookSubmit} className="space-y-4">
              <div>
                <label className="block text-xs font-medium text-slate-300 mb-1">Select Service</label>
                <select
                  value={selectedServiceId}
                  onChange={(e) => setSelectedServiceId(e.target.value)}
                  className="w-full bg-slate-950 border border-slate-800 rounded-xl px-3 py-2 text-xs text-slate-200 focus:outline-none focus:border-emerald-500"
                >
                  {services.map((s) => (
                    <option key={s.id} value={s.id}>
                      {s.name} ({s.duration_minutes}m — ₹{s.price})
                    </option>
                  ))}
                </select>
              </div>

              <div>
                <label className="block text-xs font-medium text-slate-300 mb-1">Select Date</label>
                <input
                  type="date"
                  value={bookDate}
                  min={new Date().toISOString().split('T')[0]}
                  onChange={(e) => setBookDate(e.target.value)}
                  className="w-full bg-slate-950 border border-slate-800 rounded-xl px-3 py-2 text-xs text-slate-200 focus:outline-none focus:border-emerald-500"
                />
              </div>

              {/* Real Available Slots Loaded from Backend Engine */}
              <div>
                <label className="block text-xs font-medium text-slate-300 mb-1">
                  Real Available Slots (Computed from business hours & staff availability)
                </label>
                {loadingSlots ? (
                  <div className="p-4 text-center text-xs text-slate-500">Checking slot availability...</div>
                ) : availableSlots.length === 0 ? (
                  <div className="p-3 rounded-xl bg-slate-950 border border-slate-800 text-center text-xs text-slate-500">
                    No slots available on this date (check business hours or notice policy).
                  </div>
                ) : (
                  <div className="grid grid-cols-3 sm:grid-cols-4 gap-2 max-h-36 overflow-y-auto p-1">
                    {availableSlots.map((slot, i) => {
                      const isSelected = selectedSlot?.start_time === slot.start_time;
                      return (
                        <button
                          key={i}
                          type="button"
                          onClick={() => setSelectedSlot(slot)}
                          className={`py-2 px-1 rounded-xl text-xs font-mono font-semibold transition-all border ${
                            isSelected
                              ? 'bg-emerald-500 text-slate-950 border-emerald-400 shadow-md'
                              : 'bg-slate-950 text-slate-300 border-slate-800 hover:border-slate-700'
                          }`}
                        >
                          {slot.formatted_time}
                        </button>
                      );
                    })}
                  </div>
                )}
              </div>

              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block text-xs font-medium text-slate-300 mb-1">Customer Name</label>
                  <input
                    type="text"
                    required
                    value={customerName}
                    onChange={(e) => setCustomerName(e.target.value)}
                    placeholder="e.g. Vikram Seth"
                    className="w-full bg-slate-950 border border-slate-800 rounded-xl px-3 py-2 text-xs text-slate-200 focus:outline-none focus:border-emerald-500"
                  />
                </div>
                <div>
                  <label className="block text-xs font-medium text-slate-300 mb-1">Customer Phone</label>
                  <input
                    type="text"
                    required
                    value={customerPhone}
                    onChange={(e) => setCustomerPhone(e.target.value)}
                    placeholder="+919876543210"
                    className="w-full bg-slate-950 border border-slate-800 rounded-xl px-3 py-2 text-xs text-slate-200 focus:outline-none focus:border-emerald-500"
                  />
                </div>
              </div>

              <div>
                <label className="block text-xs font-medium text-slate-300 mb-1">Notes / Special Instructions</label>
                <textarea
                  rows={2}
                  value={notes}
                  onChange={(e) => setNotes(e.target.value)}
                  placeholder="e.g. First visit consultation."
                  className="w-full bg-slate-950 border border-slate-800 rounded-xl px-3 py-2 text-xs text-slate-200 focus:outline-none focus:border-emerald-500"
                />
              </div>

              <div className="flex justify-end gap-2 pt-2 border-t border-slate-800">
                <button
                  type="button"
                  onClick={() => setIsBookModalOpen(false)}
                  className="px-4 py-2 rounded-xl bg-slate-800 text-xs text-slate-300"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={!selectedSlot}
                  className="px-4 py-2 rounded-xl bg-emerald-500 hover:bg-emerald-600 disabled:opacity-50 text-slate-950 font-bold text-xs shadow-lg shadow-emerald-500/10"
                >
                  Confirm Booking
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* Cancel Modal */}
      {cancelAppt && (
        <div className="fixed inset-0 z-50 bg-black/70 backdrop-blur-sm flex items-center justify-center p-4">
          <div className="bg-slate-900 border border-slate-800 rounded-2xl max-w-sm w-full p-6 space-y-4">
            <h3 className="font-bold text-base text-white">Cancel Appointment</h3>
            <p className="text-xs text-slate-400">
              Are you sure you want to cancel the booking for {cancelAppt.customer_name}?
            </p>
            <div>
              <label className="block text-xs font-medium text-slate-300 mb-1">Reason for Cancellation</label>
              <input
                type="text"
                value={cancelReason}
                onChange={(e) => setCancelReason(e.target.value)}
                className="w-full bg-slate-950 border border-slate-800 rounded-xl px-3 py-2 text-xs text-slate-200 focus:outline-none"
              />
            </div>
            <div className="flex justify-end gap-2 pt-2">
              <button
                type="button"
                onClick={() => setCancelAppt(null)}
                className="px-3 py-1.5 rounded-xl bg-slate-800 text-xs text-slate-300"
              >
                Keep Booking
              </button>
              <button
                type="button"
                onClick={handleCancelSubmit}
                className="px-3 py-1.5 rounded-xl bg-rose-500 hover:bg-rose-600 text-white font-bold text-xs"
              >
                Confirm Cancellation
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
