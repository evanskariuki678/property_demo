export type UserRole = 'admin' | 'landlord' | 'agent' | 'tenant';

export interface User {
  id: string;
  email: string;
  full_name: string;
  phone: string;
  role: UserRole;
  id_number?: string;
  kra_pin?: string;
  is_active: boolean;
  language: string;
  created_at: string;
}

export interface AuthResponse {
  access_token: string;
  token_type: string;
  user: User;
}

export interface Property {
  id: string;
  name: string;
  address: string;
  city: string;
  county: string;
  property_type: string;
  description?: string;
  total_units: number;
  owner_id: string;
  manager_id?: string;
  owner_name?: string;
  manager_name?: string;
  created_at: string;
}

export interface Unit {
  id: string;
  property_id: string;
  unit_number: string;
  unit_type: string;
  bedrooms: number;
  bathrooms: number;
  rent_amount: number;
  deposit_amount: number;
  status: 'vacant' | 'occupied' | 'maintenance' | 'reserved';
  floor_number?: number;
  area_sqft?: number;
  amenities?: string;
  property_name?: string;
  created_at: string;
}

export interface Lease {
  id: string;
  unit_id: string;
  tenant_id: string;
  start_date: string;
  end_date: string;
  rent_amount: number;
  deposit_amount: number;
  status: 'active' | 'expired' | 'terminated' | 'pending';
  terms?: string;
  unit_number?: string;
  property_name?: string;
  tenant_name?: string;
  tenant_email?: string;
  created_at: string;
}

export interface Payment {
  id: string;
  lease_id: string;
  amount: number;
  payment_date?: string;
  due_date: string;
  payment_method?: 'mpesa' | 'bank_transfer' | 'cash' | 'cheque';
  transaction_ref?: string;
  status: 'pending' | 'completed' | 'failed' | 'cancelled';
  paid_by: string;
  tenant_name?: string;
  unit_number?: string;
  property_name?: string;
  created_at: string;
}

export interface MaintenanceRequest {
  id: string;
  unit_id: string;
  title: string;
  description: string;
  priority: 'low' | 'medium' | 'high' | 'urgent';
  status: 'open' | 'in_progress' | 'completed' | 'cancelled';
  submitted_by: string;
  assigned_to?: string;
  resolution_notes?: string;
  unit_number?: string;
  property_name?: string;
  submitter_name?: string;
  created_at: string;
  updated_at: string;
}

export interface Document {
  id: string;
  name: string;
  document_type: string;
  file_path: string;
  entity_type: string;
  entity_id: string;
  uploaded_by: string;
  uploader_name?: string;
  created_at: string;
}

export interface Expense {
  id: string;
  property_id: string;
  category: string;
  description: string;
  amount: number;
  date: string;
  vendor?: string;
  receipt_ref?: string;
  created_by: string;
  property_name?: string;
  created_at: string;
}

export interface DashboardStats {
  total_properties: number;
  total_units: number;
  occupied_units: number;
  vacant_units: number;
  occupancy_rate: number;
  total_tenants: number;
  total_revenue: number;
  pending_payments: number;
  overdue_payments: number;
  active_leases: number;
  expiring_leases: number;
  open_maintenance: number;
  monthly_revenue: { month: string; revenue: number }[];
  recent_payments: {
    id: string;
    tenant: string;
    amount: number;
    date: string;
    method: string;
    status: string;
  }[];
  recent_maintenance: {
    id: string;
    title: string;
    submitted_by: string;
    status: string;
    priority: string;
    date: string;
  }[];
}
