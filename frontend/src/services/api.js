import axios from 'axios';

// Create axios instance
// In local dev, falls back to the relative path which Vite's dev server
// proxies to localhost:8000 (see vite.config.js). In production (Vercel),
// there is no such proxy, so VITE_API_URL must point at the deployed backend.
const api = axios.create({
  baseURL: import.meta.env.VITE_API_URL || '/api/v1',
  headers: {
    'Content-Type': 'application/json',
  },
});

// Request interceptor - add token to requests
api.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('token');
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);

// Response interceptor - handle errors
api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      // Unauthorized - clear token and redirect to login
      localStorage.removeItem('token');
      localStorage.removeItem('user');
      window.location.href = '/login';
    }
    return Promise.reject(error);
  }
);

// Auth API
export const authAPI = {
  login: ({ username, password }) => {
    const formData = new URLSearchParams();
    formData.append("username", username);
    formData.append("password", password);

    return api.post("/auth/login", formData, {
      headers: {
        "Content-Type": "application/x-www-form-urlencoded",
      },
    });
  },

  me: () => api.get('/auth/me'),
  changePassword: (data) => api.post('/auth/change-password', data),
};
// Users API
export const usersAPI = {
  getAll: (params) => api.get('/users/', { params }),
  getById: (id) => api.get(`/users/${id}`),
  create: (data) => api.post('/users/', data),
  update: (id, data) => api.put(`/users/${id}`, data),
  delete: (id) => api.delete(`/users/${id}`),
};

// Patients API
export const patientsAPI = {
  getAll: (params) => api.get('/patients/', { params }),
  getById: (id) => api.get(`/patients/${id}`),
  create: (data) => api.post('/patients/', data),
  update: (id, data) => api.put(`/patients/${id}`, data),
  delete: (id) => api.delete(`/patients/${id}`),
  getCount: () => api.get('/patients/stats/count'),
};

// Medicines API
export const medicinesAPI = {
  getAll: (params) => api.get('/medicines/', { params }),
  getById: (id) => api.get(`/medicines/${id}`),
  create: (data) => api.post('/medicines/', data),
  update: (id, data) => api.put(`/medicines/${id}`, data),
  delete: (id) => api.delete(`/medicines/${id}`),
  getCategories: () => api.get('/medicines/categories'),
  getStats: () => api.get('/medicines/stats/summary'),
};

// Inventory API
export const inventoryAPI = {
  getAll: (params) => api.get('/inventory/', { params }),
  getWithDetails: (params) => api.get('/inventory/with-details', { params }),
  create: (data) => api.post('/inventory/', data),
  update: (id, data) => api.put(`/inventory/${id}`, data),
  getLowStock: () => api.get('/inventory/alerts/low-stock'),
  getExpiring: (days) => api.get('/inventory/alerts/expiring', { params: { days } }),
  getExpired: () => api.get('/inventory/alerts/expired'),
  getStats: () => api.get('/inventory/stats/summary'),
};

// Vendors API
export const vendorsAPI = {
  getAll: (params) => api.get('/vendors/', { params }),
  getById: (id) => api.get(`/vendors/${id}`),
  create: (data) => api.post('/vendors/', data),
  update: (id, data) => api.put(`/vendors/${id}`, data),
  delete: (id) => api.delete(`/vendors/${id}`),
  getPerformance: (id) => api.get(`/vendors/${id}/performance`),
  updateRating: (id, rating) => api.put(`/vendors/${id}/rating`, null, { params: { rating } }),
  getStats: () => api.get('/vendors/stats/summary'),
};

// Procurement API
export const procurementAPI = {
  getAll: (params) => api.get('/procurement/', { params }),
  getById: (id) => api.get(`/procurement/${id}`),
  create: (data) => api.post('/procurement/', data),
  approve: (id) => api.put(`/procurement/${id}/approve`),
  markOrdered: (id) => api.put(`/procurement/${id}/mark-ordered`),
  receive: (id, items) => api.put(`/procurement/${id}/receive`, items),
  cancel: (id, reason) => api.put(`/procurement/${id}/cancel`, null, { params: { reason } }),
  getStats: () => api.get('/procurement/stats/summary'),
};

// Appointments API
export const appointmentsAPI = {
  getAll: (params) => api.get('/appointments/', { params }),
  getById: (id) => api.get(`/appointments/${id}`),
  getToday: (timeSlot) => api.get('/appointments/today', { params: { time_slot: timeSlot } }),
  create: (data) => api.post('/appointments/', data),
  update: (id, data) => api.put(`/appointments/${id}`, data),
  updateStatus: (id, status) => api.put(`/appointments/${id}/status/${status}`),
  delete: (id) => api.delete(`/appointments/${id}`),
  getStats: () => api.get('/appointments/stats/summary'),
};

// Billing API
export const billingAPI = {
  getAll: (params) => api.get('/billing/', { params }),
  getById: (id) => api.get(`/billing/${id}`),
  getByNumber: (billNumber) => api.get(`/billing/number/${billNumber}`),
  getToday: () => api.get('/billing/today'),
  create: (data) => api.post('/billing/', data),
  updatePayment: (id, amount, paymentMode) => 
    api.put(`/billing/${id}/payment`, null, { params: { amount_paid: amount, payment_mode: paymentMode } }),
  getPatientHistory: (patientId) => api.get(`/billing/patient/${patientId}/history`),
  getStats: (params) => api.get('/billing/stats/summary', { params }),
};

// Reports API
export const reportsAPI = {
  getDashboard: () => api.get('/reports/dashboard'),
  getFinancial: (params) => api.get('/reports/financial', { params }),
  getInventory: (params) => api.get('/reports/inventory', { params }),
  getPatientVisits: (params) => api.get('/reports/patient-visits', { params }),
  getProcurement: (params) => api.get('/reports/procurement', { params }),
  exportFinancial: (params) => api.get('/reports/export/financial', { params }),
};

// Chatbot API
export const chatbotAPI = {
  chat: (data) => api.post('/chatbot/chat', data),
  getHistory: (sessionId, limit) => api.get(`/chatbot/history/${sessionId}`, { params: { limit } }),
  getSessions: (limit) => api.get('/chatbot/sessions', { params: { limit } }),
  deleteSession: (sessionId) => api.delete(`/chatbot/session/${sessionId}`),
  rebuildKnowledgeBase: () => api.post('/chatbot/rebuild-knowledge-base'),
  getStats: () => api.get('/chatbot/stats'),
  health: () => api.get('/chatbot/health'),
};

export default api;