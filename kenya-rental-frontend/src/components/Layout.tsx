import { useState } from 'react';
import { Link, useLocation, Outlet, useNavigate } from 'react-router-dom';
import { useAuth } from '@/contexts/AuthContext';
import { Button } from '@/components/ui/button';
import {
  Home,
  Building2,
  DoorOpen,
  Users,
  FileText,
  CreditCard,
  Wrench,
  BarChart3,
  FolderOpen,
  Settings,
  LogOut,
  Menu,
  X,
  Bell,
} from 'lucide-react';

const navItems = [
  { path: '/dashboard', label: 'Dashboard', icon: Home, roles: ['admin', 'landlord', 'agent', 'tenant'] },
  { path: '/properties', label: 'Properties', icon: Building2, roles: ['admin', 'landlord', 'agent'] },
  { path: '/units', label: 'Units', icon: DoorOpen, roles: ['admin', 'landlord', 'agent'] },
  { path: '/tenants', label: 'Tenants', icon: Users, roles: ['admin', 'landlord', 'agent'] },
  { path: '/leases', label: 'Leases', icon: FileText, roles: ['admin', 'landlord', 'agent', 'tenant'] },
  { path: '/payments', label: 'Payments', icon: CreditCard, roles: ['admin', 'landlord', 'agent', 'tenant'] },
  { path: '/maintenance', label: 'Maintenance', icon: Wrench, roles: ['admin', 'landlord', 'agent', 'tenant'] },
  { path: '/reports', label: 'Reports', icon: BarChart3, roles: ['admin', 'landlord', 'agent'] },
  { path: '/documents', label: 'Documents', icon: FolderOpen, roles: ['admin', 'landlord', 'agent', 'tenant'] },
  { path: '/settings', label: 'Settings', icon: Settings, roles: ['admin', 'landlord', 'agent', 'tenant'] },
];

export default function Layout() {
  const { user, logout } = useAuth();
  const location = useLocation();
  const navigate = useNavigate();
  const [sidebarOpen, setSidebarOpen] = useState(false);

  const filteredNav = navItems.filter((item) => user && item.roles.includes(user.role));

  const handleLogout = () => {
    logout();
    navigate('/login');
  };

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Mobile header */}
      <div className="lg:hidden fixed top-0 left-0 right-0 z-40 bg-white border-b px-4 py-3 flex items-center justify-between">
        <button onClick={() => setSidebarOpen(true)} className="p-1">
          <Menu className="h-6 w-6" />
        </button>
        <div className="flex items-center gap-2">
          <Building2 className="h-6 w-6 text-green-700" />
          <span className="font-bold text-green-800">KenyaRentals</span>
        </div>
        <button className="p-1 relative">
          <Bell className="h-5 w-5 text-gray-600" />
        </button>
      </div>

      {/* Mobile sidebar overlay */}
      {sidebarOpen && (
        <div className="lg:hidden fixed inset-0 z-50 bg-black/50" onClick={() => setSidebarOpen(false)}>
          <div className="w-64 h-full bg-white" onClick={(e) => e.stopPropagation()}>
            <SidebarContent
              filteredNav={filteredNav}
              location={location}
              user={user}
              onClose={() => setSidebarOpen(false)}
              onLogout={handleLogout}
            />
          </div>
        </div>
      )}

      {/* Desktop sidebar */}
      <div className="hidden lg:fixed lg:inset-y-0 lg:flex lg:w-64 lg:flex-col">
        <SidebarContent
          filteredNav={filteredNav}
          location={location}
          user={user}
          onLogout={handleLogout}
        />
      </div>

      {/* Main content */}
      <div className="lg:pl-64">
        <main className="pt-16 lg:pt-0">
          <div className="p-4 lg:p-8">
            <Outlet />
          </div>
        </main>
      </div>
    </div>
  );
}

function SidebarContent({
  filteredNav,
  location,
  user,
  onClose,
  onLogout,
}: {
  filteredNav: typeof navItems;
  location: { pathname: string };
  user: { full_name: string; role: string; email: string } | null;
  onClose?: () => void;
  onLogout: () => void;
}) {
  return (
    <div className="flex flex-col h-full bg-white border-r">
      {/* Logo */}
      <div className="p-4 border-b flex items-center justify-between">
        <div className="flex items-center gap-2">
          <Building2 className="h-8 w-8 text-green-700" />
          <div>
            <h1 className="font-bold text-green-800 text-lg">KenyaRentals</h1>
            <p className="text-xs text-gray-500">Property Management</p>
          </div>
        </div>
        {onClose && (
          <button onClick={onClose} className="lg:hidden p-1">
            <X className="h-5 w-5" />
          </button>
        )}
      </div>

      {/* Nav items */}
      <nav className="flex-1 p-3 space-y-1 overflow-y-auto">
        {filteredNav.map((item) => {
          const isActive = location.pathname === item.path;
          const Icon = item.icon;
          return (
            <Link
              key={item.path}
              to={item.path}
              onClick={onClose}
              className={`flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm font-medium transition-colors ${
                isActive
                  ? 'bg-green-50 text-green-700 border border-green-200'
                  : 'text-gray-600 hover:bg-gray-100 hover:text-gray-900'
              }`}
            >
              <Icon className="h-5 w-5 flex-shrink-0" />
              {item.label}
            </Link>
          );
        })}
      </nav>

      {/* User info */}
      <div className="p-4 border-t">
        <div className="flex items-center gap-3 mb-3">
          <div className="h-9 w-9 rounded-full bg-green-100 flex items-center justify-center text-green-700 font-semibold text-sm">
            {user?.full_name?.charAt(0) || 'U'}
          </div>
          <div className="flex-1 min-w-0">
            <p className="text-sm font-medium truncate">{user?.full_name}</p>
            <p className="text-xs text-gray-500 capitalize">{user?.role}</p>
          </div>
        </div>
        <Button variant="ghost" size="sm" className="w-full justify-start text-red-600 hover:text-red-700 hover:bg-red-50" onClick={onLogout}>
          <LogOut className="h-4 w-4 mr-2" />
          Sign Out
        </Button>
      </div>
    </div>
  );
}
