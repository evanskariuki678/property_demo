import { useEffect, useState } from 'react';
import { useAuth } from '@/contexts/AuthContext';
import { getDashboard } from '@/services/api';
import { DashboardStats } from '@/types';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table';
import {
  Building2, DoorOpen, Users, CreditCard, Wrench, FileText, TrendingUp, AlertTriangle,
} from 'lucide-react';
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts';

export default function Dashboard() {
  const { user } = useAuth();
  const [stats, setStats] = useState<DashboardStats | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    getDashboard()
      .then((res) => setStats(res.data))
      .catch(console.error)
      .finally(() => setLoading(false));
  }, []);

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-96">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-green-700" />
      </div>
    );
  }

  if (!stats) return <p className="text-gray-500">Failed to load dashboard data.</p>;

  const statCards = [
    { label: 'Properties', value: stats.total_properties, icon: Building2, color: 'text-blue-600', bg: 'bg-blue-50' },
    { label: 'Total Units', value: stats.total_units, icon: DoorOpen, color: 'text-purple-600', bg: 'bg-purple-50' },
    { label: 'Occupancy', value: `${stats.occupancy_rate}%`, icon: TrendingUp, color: 'text-green-600', bg: 'bg-green-50' },
    { label: 'Tenants', value: stats.total_tenants, icon: Users, color: 'text-orange-600', bg: 'bg-orange-50' },
    { label: 'Revenue (KES)', value: stats.total_revenue.toLocaleString(), icon: CreditCard, color: 'text-green-600', bg: 'bg-green-50' },
    { label: 'Pending (KES)', value: stats.pending_payments.toLocaleString(), icon: AlertTriangle, color: 'text-yellow-600', bg: 'bg-yellow-50' },
    { label: 'Active Leases', value: stats.active_leases, icon: FileText, color: 'text-indigo-600', bg: 'bg-indigo-50' },
    { label: 'Open Tickets', value: stats.open_maintenance, icon: Wrench, color: 'text-red-600', bg: 'bg-red-50' },
  ];

  const filteredCards = user?.role === 'tenant'
    ? statCards.filter((c) => ['Revenue (KES)', 'Pending (KES)', 'Active Leases', 'Open Tickets'].includes(c.label))
    : statCards;

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-gray-900">
          {user?.role === 'tenant' ? 'My Dashboard' : 'Dashboard'}
        </h1>
        <p className="text-gray-500 mt-1">Welcome back, {user?.full_name}</p>
      </div>

      {/* Stat cards */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
        {filteredCards.map((stat) => {
          const Icon = stat.icon;
          return (
            <Card key={stat.label}>
              <CardContent className="p-4">
                <div className="flex items-center justify-between">
                  <div>
                    <p className="text-xs font-medium text-gray-500">{stat.label}</p>
                    <p className="text-xl font-bold mt-1">{stat.value}</p>
                  </div>
                  <div className={`p-2 rounded-lg ${stat.bg}`}>
                    <Icon className={`h-5 w-5 ${stat.color}`} />
                  </div>
                </div>
              </CardContent>
            </Card>
          );
        })}
      </div>

      {/* Revenue Chart */}
      {user?.role !== 'tenant' && (
        <Card>
          <CardHeader>
            <CardTitle className="text-base">Monthly Revenue (KES)</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="h-64">
              <ResponsiveContainer width="100%" height="100%">
                <BarChart data={stats.monthly_revenue}>
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis dataKey="month" tick={{ fontSize: 12 }} />
                  <YAxis tick={{ fontSize: 12 }} />
                  <Tooltip formatter={(value: number) => [`KES ${value.toLocaleString()}`, 'Revenue']} />
                  <Bar dataKey="revenue" fill="#15803d" radius={[4, 4, 0, 0]} />
                </BarChart>
              </ResponsiveContainer>
            </div>
          </CardContent>
        </Card>
      )}

      {/* Recent tables */}
      <div className="grid lg:grid-cols-2 gap-6">
        {/* Recent Payments */}
        <Card>
          <CardHeader>
            <CardTitle className="text-base">Recent Payments</CardTitle>
          </CardHeader>
          <CardContent>
            {stats.recent_payments.length === 0 ? (
              <p className="text-sm text-gray-500">No recent payments</p>
            ) : (
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead>Tenant</TableHead>
                    <TableHead>Amount</TableHead>
                    <TableHead>Method</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {stats.recent_payments.map((p) => (
                    <TableRow key={p.id}>
                      <TableCell className="font-medium">{p.tenant}</TableCell>
                      <TableCell>KES {p.amount.toLocaleString()}</TableCell>
                      <TableCell>
                        <Badge variant="secondary" className="capitalize">{p.method.replace('_', ' ')}</Badge>
                      </TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            )}
          </CardContent>
        </Card>

        {/* Recent Maintenance */}
        <Card>
          <CardHeader>
            <CardTitle className="text-base">Recent Maintenance</CardTitle>
          </CardHeader>
          <CardContent>
            {stats.recent_maintenance.length === 0 ? (
              <p className="text-sm text-gray-500">No maintenance requests</p>
            ) : (
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead>Issue</TableHead>
                    <TableHead>Priority</TableHead>
                    <TableHead>Status</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {stats.recent_maintenance.map((m) => (
                    <TableRow key={m.id}>
                      <TableCell className="font-medium">{m.title}</TableCell>
                      <TableCell>
                        <Badge variant={m.priority === 'urgent' ? 'destructive' : m.priority === 'high' ? 'warning' : 'secondary'}>
                          {m.priority}
                        </Badge>
                      </TableCell>
                      <TableCell>
                        <Badge variant={m.status === 'completed' ? 'default' : m.status === 'in_progress' ? 'info' : 'warning'}>
                          {m.status.replace('_', ' ')}
                        </Badge>
                      </TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            )}
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
