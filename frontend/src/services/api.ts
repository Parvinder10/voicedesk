const API_BASE = '/api/v1';

export class ApiError extends Error {
  status: number;
  data: any;

  constructor(status: number, message: string, data?: any) {
    super(message);
    this.status = status;
    this.data = data;
  }
}

async function request<T = any>(endpoint: string, options: RequestInit = {}): Promise<T> {
  const token = localStorage.getItem('voicedesk_token');
  const headers = new Headers(options.headers || {});

  if (token && !headers.has('Authorization')) {
    headers.set('Authorization', `Bearer ${token}`);
  }

  if (!(options.body instanceof FormData) && !headers.has('Content-Type')) {
    headers.set('Content-Type', 'application/json');
  }

  const response = await fetch(`${API_BASE}${endpoint}`, {
    ...options,
    headers,
  });

  if (response.status === 401 && !endpoint.includes('/auth/login')) {
    // Attempt token refresh or logout
    const refreshToken = localStorage.getItem('voicedesk_refresh_token');
    if (refreshToken && !endpoint.includes('/auth/refresh')) {
      try {
        const refreshRes = await fetch(`${API_BASE}/auth/refresh`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ refresh_token: refreshToken }),
        });
        if (refreshRes.ok) {
          const tokenData = await refreshRes.json();
          localStorage.setItem('voicedesk_token', tokenData.access_token);
          if (tokenData.refresh_token) {
            localStorage.setItem('voicedesk_refresh_token', tokenData.refresh_token);
          }
          headers.set('Authorization', `Bearer ${tokenData.access_token}`);
          const retryRes = await fetch(`${API_BASE}${endpoint}`, { ...options, headers });
          if (!retryRes.ok) {
            const errData = await retryRes.json().catch(() => ({}));
            throw new ApiError(retryRes.status, errData.detail || 'Request failed', errData);
          }
          return retryRes.json();
        }
      } catch (e) {
        // Fall through
      }
    }
    localStorage.removeItem('voicedesk_token');
    localStorage.removeItem('voicedesk_refresh_token');
    localStorage.removeItem('voicedesk_user');
  }

  if (!response.ok) {
    const errorData = await response.json().catch(() => ({}));
    const message = errorData.detail || `Request failed with status ${response.status}`;
    throw new ApiError(response.status, message, errorData);
  }

  return response.json();
}

export const api = {
  // Auth
  register: (data: any) => request('/auth/register', { method: 'POST', body: JSON.stringify(data) }),
  login: (data: any) => request('/auth/login', { method: 'POST', body: JSON.stringify(data) }),
  getMe: () => request('/auth/me'),

  // Dashboard
  getDashboardOverview: () => request('/dashboard/overview'),
  getDashboardActivity: (limit = 10) => request(`/dashboard/activity?limit=${limit}`),

  // Customers
  getCustomers: (q?: string, skip = 0, limit = 50) => {
    const query = q ? `?q=${encodeURIComponent(q)}&skip=${skip}&limit=${limit}` : `?skip=${skip}&limit=${limit}`;
    return request(`/customers${query}`);
  },
  getCustomer: (id: string) => request(`/customers/${id}`),
  createCustomer: (data: any) => request('/customers', { method: 'POST', body: JSON.stringify(data) }),
  updateCustomer: (id: string, data: any) => request(`/customers/${id}`, { method: 'PATCH', body: JSON.stringify(data) }),

  // Services
  getServices: () => request('/services'),
  createService: (data: any) => request('/services', { method: 'POST', body: JSON.stringify(data) }),
  updateService: (id: string, data: any) => request(`/services/${id}`, { method: 'PATCH', body: JSON.stringify(data) }),
  deleteService: (id: string) => request(`/services/${id}`, { method: 'DELETE' }),

  // Staff
  getStaff: () => request('/staff'),
  createStaff: (data: any) => request('/staff', { method: 'POST', body: JSON.stringify(data) }),
  updateStaff: (id: string, data: any) => request(`/staff/${id}`, { method: 'PATCH', body: JSON.stringify(data) }),
  deleteStaff: (id: string) => request(`/staff/${id}`, { method: 'DELETE' }),

  // Availability & Booking
  getAvailability: (serviceId: string, date: string, staffId?: string) => {
    let url = `/availability?service_id=${serviceId}&date=${date}`;
    if (staffId) url += `&staff_id=${staffId}`;
    return request(url);
  },
  getAvailabilityRules: () => request('/availability/rules'),
  createAvailabilityRule: (data: any) => request('/availability/rules', { method: 'POST', body: JSON.stringify(data) }),

  // Appointments
  getAppointments: (params: { status?: string; customer_id?: string; staff_id?: string; start_date?: string; end_date?: string } = {}) => {
    const q = new URLSearchParams();
    if (params.status) q.append('status', params.status);
    if (params.customer_id) q.append('customer_id', params.customer_id);
    if (params.staff_id) q.append('staff_id', params.staff_id);
    if (params.start_date) q.append('start_date', params.start_date);
    if (params.end_date) q.append('end_date', params.end_date);
    return request(`/appointments?${q.toString()}`);
  },
  getAppointment: (id: string) => request(`/appointments/${id}`),
  bookAppointment: (data: any) => request('/appointments', { method: 'POST', body: JSON.stringify(data) }),
  updateAppointment: (id: string, data: any) => request(`/appointments/${id}`, { method: 'PATCH', body: JSON.stringify(data) }),
  rescheduleAppointment: (id: string, data: any) => request(`/appointments/${id}/reschedule`, { method: 'POST', body: JSON.stringify(data) }),
  cancelAppointment: (id: string, data: any) => request(`/appointments/${id}/cancel`, { method: 'POST', body: JSON.stringify(data) }),

  // Calls
  getCalls: (params: { status?: string; outcome?: string; customer_id?: string; skip?: number; limit?: number } = {}) => {
    const q = new URLSearchParams();
    if (params.status) q.append('status', params.status);
    if (params.outcome) q.append('outcome', params.outcome);
    if (params.customer_id) q.append('customer_id', params.customer_id);
    if (params.skip) q.append('skip', String(params.skip));
    if (params.limit) q.append('limit', String(params.limit));
    return request(`/calls?${q.toString()}`);
  },
  getCall: (id: string) => request(`/calls/${id}`),
  getCallTranscript: (id: string) => request(`/calls/${id}/transcript`),

  // Knowledge & RAG
  getDocuments: () => request('/knowledge/documents'),
  uploadDocument: (file: File) => {
    const formData = new FormData();
    formData.append('file', file);
    return request('/knowledge/documents', { method: 'POST', body: formData });
  },
  deleteDocument: (id: string) => request(`/knowledge/documents/${id}`, { method: 'DELETE' }),
  reindexDocument: (id: string) => request(`/knowledge/reindex/${id}`, { method: 'POST' }),
  queryKnowledge: (query: string, top_k = 4) => request('/knowledge/query', { method: 'POST', body: JSON.stringify({ query, top_k }) }),

  // Settings & Hours
  getSettings: () => request('/settings'),
  updateSettings: (data: any) => request('/settings', { method: 'PATCH', body: JSON.stringify(data) }),
  getHours: () => request('/settings/hours'),
  updateHours: (data: any) => request('/settings/hours', { method: 'PUT', body: JSON.stringify(data) }),
  getHolidays: () => request('/settings/holidays'),
  addHoliday: (data: any) => request('/settings/holidays', { method: 'POST', body: JSON.stringify(data) }),
  deleteHoliday: (id: string) => request(`/settings/holidays/${id}`, { method: 'DELETE' }),

  // Vapi Voice Integration
  getVapiHealth: () => request('/vapi/health'),
  syncAssistantConfig: () => request('/vapi/assistant/sync', { method: 'POST' }),
  testSimulateCallWebhook: (payload: any) => request('/vapi/webhook', { method: 'POST', body: JSON.stringify(payload) }),
};
