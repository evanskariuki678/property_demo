import { useEffect, useState } from 'react';
import { getDashboard, getPayments, getExpenses } from '@/services/api';
import { DashboardStats, Payment, Expense } from '@/types';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table';
import { Badge } from '@/components/ui/badge';
import {
  BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer,
  PieChart, Pie, Cell, Legend,
} from 'recharts';
import { TrendingUp, DollarSign, Home, Users } from 'lucide-react';

const COLORS = ['#15803d', '#dc2626', '#f59e0b', '#3b82f6', '#8b5cf6'];

export default function Reports() {
  const [stats, setStats] = useState<DashboardStats | null>(null);
  const [payments, setPayments] = useState<Payment[]>([]);
  const [expenses, setExpenses] = useState<Expense[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    Promise.all([getDashboard(), getPayments(), getExpenses()])
      .then(([s, p, e]) => { setStats(s.data); setPayments(p.data); setExpenses(e.data); })
      .catch(console.error).finally(() => setLoading(false));
  }, []);

  if (loading) return <div className="flex items-center justify-center min-h-96"><div className="animate-spin rounded-full h-8 w-8 border-b-2 border-green-700" /></div>;
  if (!stats) return <p className="text-gray-500">Failed to load reports data.</p>;

  const occupancyData = [
    { name: 'Occupied', value: stats.occupied_units },
    { name: 'Vacant', value: stats.vacant_units },
  ];

  const totalExpenses = expenses.reduce((sum, e) => sum + e.amount, 0);
  const netIncome = stats.total_revenue - totalExpenses;

  const summaryCards = [
    { label: 'Total Revenue', value: `KES ${stats.total_revenue.toLocaleString()}`, icon: DollarSign, color: 'text-green-600', bg: 'bg-green-50' },
    { label: 'Total Expenses', value: `KES ${totalExpenses.toLocaleString()}`, icon: TrendingUp, color: 'text-red-600', bg: 'bg-red-50' },
    { label: 'Net Income', value: `KES ${netIncome.toLocaleString()}`, icon: DollarSign, color: netIncome >= 0 ? 'text-green-600' : 'text-red-600', bg: netIncome >= 0 ? 'bg-green-50' : 'bg-red-50' },
    { label: 'Occupancy Rate', value: `${stats.occupancy_rate}%`, icon: Home, color: 'text-blue-600', bg: 'bg-blue-50' },
  ];

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-gray-900">Reports & Analytics</h1>
        <p className="text-gray-500 mt-1">Financial overview and property analytics</p>
      </div>

      {/* Summary */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
        {summaryCards.map((s) => {
          const Icon = s.icon;
          return (
            <Card key={s.label}>
              <CardContent className="p-4">
                <div className="flex items-center justify-between">
                  <div>
                    <p className="text-xs font-medium text-gray-500">{s.label}</p>
                    <p className="text-lg font-bold mt-1">{s.value}</p>
                  </div>
                  <div className={`p-2 rounded-lg ${s.bg}`}><Icon className={`h-5 w-5 ${s.color}`} /></div>
                </div>
              </CardContent>
            </Card>
          );
        })}
      </div>

      <Tabs defaultValue="revenue">
        <TabsList>
          <TabsTrigger value="revenue">Revenue</TabsTrigger>
          <TabsTrigger value="occupancy">Occupancy</TabsTrigger>
          <TabsTrigger value="payments">Payment History</TabsTrigger>
          <TabsTrigger value="expenses">Expenses</TabsTrigger>
        </TabsList>

        <TabsContent value="revenue">
          <Card>
            <CardHeader><CardTitle className="text-base">Monthly Revenue (KES)</CardTitle></CardHeader>
            <CardContent>
              <div className="h-72">
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
        </TabsContent>

        <TabsContent value="occupancy">
          <Card>
            <CardHeader><CardTitle className="text-base">Occupancy Overview</CardTitle></CardHeader>
            <CardContent>
              <div className="grid md:grid-cols-2 gap-6">
                <div className="h-64">
                  <ResponsiveContainer width="100%" height="100%">
                    <PieChart>
                      <Pie data={occupancyData} cx="50%" cy="50%" innerRadius={60} outerRadius={80} paddingAngle={5} dataKey="value" label={({ name, percent }) => `${name} ${(percent * 100).toFixed(0)}%`}>
                        {occupancyData.map((_, i) => <Cell key={i} fill={COLORS[i]} />)}
                      </Pie>
                      <Legend />
                    </PieChart>
                  </ResponsiveContainer>
                </div>
                <div className="space-y-4">
                  <div className="p-4 bg-green-50 rounded-lg">
                    <p className="text-sm text-gray-600">Occupied Units</p>
                    <p className="text-2xl font-bold text-green-700">{stats.occupied_units}</p>
                  </div>
                  <div className="p-4 bg-red-50 rounded-lg">
                    <p className="text-sm text-gray-600">Vacant Units</p>
                    <p className="text-2xl font-bold text-red-600">{stats.vacant_units}</p>
                  </div>
                  <div className="p-4 bg-blue-50 rounded-lg flex items-center gap-2">
                    <Users className="h-5 w-5 text-blue-600" />
                    <div>
                      <p className="text-sm text-gray-600">Active Tenants</p>
                      <p className="text-xl font-bold text-blue-700">{stats.total_tenants}</p>
                    </div>
                  </div>
                </div>
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="payments">
          <Card>
            <CardContent className="p-0">
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead>Tenant</TableHead>
                    <TableHead>Amount (KES)</TableHead>
                    <TableHead className="hidden md:table-cell">Date</TableHead>
                    <TableHead>Method</TableHead>
                    <TableHead>Status</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {payments.slice(0, 20).map((p) => (
                    <TableRow key={p.id}>
                      <TableCell className="font-medium">{p.tenant_name || '-'}</TableCell>
                      <TableCell>{p.amount.toLocaleString()}</TableCell>
                      <TableCell className="hidden md:table-cell">{p.payment_date ? new Date(p.payment_date).toLocaleDateString() : '-'}</TableCell>
                      <TableCell className="capitalize">{(p.payment_method || '-').replace('_', ' ')}</TableCell>
                      <TableCell><Badge variant={p.status === 'completed' ? 'default' : 'warning'} className="capitalize">{p.status}</Badge></TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="expenses">
          <Card>
            <CardContent className="p-0">
              {expenses.length === 0 ? (
                <p className="p-8 text-center text-gray-500">No expenses recorded</p>
              ) : (
                <Table>
                  <TableHeader>
                    <TableRow>
                      <TableHead>Category</TableHead>
                      <TableHead>Description</TableHead>
                      <TableHead className="hidden md:table-cell">Property</TableHead>
                      <TableHead>Amount (KES)</TableHead>
                      <TableHead className="hidden md:table-cell">Date</TableHead>
                    </TableRow>
                  </TableHeader>
                  <TableBody>
                    {expenses.map((e) => (
                      <TableRow key={e.id}>
                        <TableCell className="capitalize font-medium">{e.category}</TableCell>
                        <TableCell>{e.description}</TableCell>
                        <TableCell className="hidden md:table-cell">{e.property_name || '-'}</TableCell>
                        <TableCell>{e.amount.toLocaleString()}</TableCell>
                        <TableCell className="hidden md:table-cell">{new Date(e.date).toLocaleDateString()}</TableCell>
                      </TableRow>
                    ))}
                  </TableBody>
                </Table>
              )}
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>
    </div>
  );
}
