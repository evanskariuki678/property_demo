import axios from 'axios';

const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

const api = axios.create({
  baseURL: API_URL,
});

api.interceptors.request.use((config) => {
  const token = localStorage.getItem('token');
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      localStorage.removeItem('token');
      localStorage.removeItem('user');
      window.location.href = '/login';
    }
    return Promise.reject(error);
  }
);

// Auth
export const login = (email: string, password: string) =>
  api.post('/api/auth/login', new URLSearchParams({ username: email, password }), {
    headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
  });

export const register = (data: {
  email: string;
  password: string;
  full_name: string;
  phone: string;
  role?: string;
  id_number?: string;
  kra_pin?: string;
}) => api.post('/api/auth/register', data);

export const getMe = () => api.get('/api/auth/me');

// Properties
export const getProperties = () => api.get('/api/properties');
export const getProperty = (id: string) => api.get(`/api/properties/${id}`);
export const createProperty = (data: Record<string, unknown>) => api.post('/api/properties', data);
export const updateProperty = (id: string, data: Record<string, unknown>) => api.put(`/api/properties/${id}`, data);
export const deleteProperty = (id: string) => api.delete(`/api/properties/${id}`);

// Units
export const getUnits = (propertyId?: string) =>
  api.get('/api/units', { params: propertyId ? { property_id: propertyId } : {} });
export const getUnit = (id: string) => api.get(`/api/units/${id}`);
export const createUnit = (data: Record<string, unknown>) => api.post('/api/units', data);
export const updateUnit = (id: string, data: Record<string, unknown>) => api.put(`/api/units/${id}`, data);
export const deleteUnit = (id: string) => api.delete(`/api/units/${id}`);

// Leases
export const getLeases = () => api.get('/api/leases');
export const getLease = (id: string) => api.get(`/api/leases/${id}`);
export const createLease = (data: Record<string, unknown>) => api.post('/api/leases', data);
export const updateLease = (id: string, data: Record<string, unknown>) => api.put(`/api/leases/${id}`, data);

// Payments
export const getPayments = () => api.get('/api/payments');
export const createPayment = (data: Record<string, unknown>) => api.post('/api/payments', data);
export const updatePaymentStatus = (id: string, status: string) =>
  api.put(`/api/payments/${id}`, { status });

// Maintenance
export const getMaintenanceRequests = () => api.get('/api/maintenance');
export const createMaintenanceRequest = (data: Record<string, unknown>) => api.post('/api/maintenance', data);
export const updateMaintenanceRequest = (id: string, data: Record<string, unknown>) =>
  api.put(`/api/maintenance/${id}`, data);

// Reports
export const getDashboard = () => api.get('/api/reports/dashboard');

// Documents
export const getDocuments = () => api.get('/api/documents');
export const uploadDocument = (data: FormData) =>
  api.post('/api/documents', data, { headers: { 'Content-Type': 'multipart/form-data' } });
export const deleteDocument = (id: string) => api.delete(`/api/documents/${id}`);

// Expenses
export const getExpenses = () => api.get('/api/expenses');
export const createExpense = (data: Record<string, unknown>) => api.post('/api/expenses', data);
export const deleteExpense = (id: string) => api.delete(`/api/expenses/${id}`);

// Tenants (users with tenant role)
export const getTenants = () => api.get('/api/auth/users?role=tenant');

// M-Pesa
export const initiateStkPush = (data: { phone_number: string; amount: number; lease_id: string }) =>
  api.post('/api/mpesa/stk-push', data);

export default api;
