import { useEffect, useState } from 'react';
import { getPayments, createPayment, getLeases, initiateStkPush } from '@/services/api';
import { Payment, Lease } from '@/types';
import { useAuth } from '@/contexts/AuthContext';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Badge } from '@/components/ui/badge';
import { Card, CardContent } from '@/components/ui/card';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table';
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogFooter } from '@/components/ui/dialog';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Plus, CreditCard, Smartphone } from 'lucide-react';

const statusColors: Record<string, 'default' | 'warning' | 'destructive' | 'info'> = {
  completed: 'default', pending: 'warning', failed: 'destructive', cancelled: 'destructive',
};

export default function Payments() {
  const { user } = useAuth();
  const [payments, setPayments] = useState<Payment[]>([]);
  const [leases, setLeases] = useState<Lease[]>([]);
  const [loading, setLoading] = useState(true);
  const [dialogOpen, setDialogOpen] = useState(false);
  const [mpesaDialog, setMpesaDialog] = useState(false);
  const [mpesaForm, setMpesaForm] = useState({ phone: '', amount: 0, lease_id: '' });
  const [mpesaLoading, setMpesaLoading] = useState(false);
  const [mpesaResult, setMpesaResult] = useState('');
  const [form, setForm] = useState({
    lease_id: '', amount: 0, due_date: '', payment_method: 'mpesa', status: 'pending',
  });

  const load = () => {
    Promise.all([getPayments(), getLeases()])
      .then(([p, l]) => { setPayments(p.data); setLeases(l.data); })
      .catch(console.error).finally(() => setLoading(false));
  };

  useEffect(load, []);

  const handleSubmit = async () => {
    try {
      await createPayment(form);
      setDialogOpen(false);
      load();
    } catch (err) { console.error(err); }
  };

  const handleMpesa = async () => {
    setMpesaLoading(true);
    setMpesaResult('');
    try {
      const res = await initiateStkPush(mpesaForm);
      setMpesaResult(res.data?.message || 'STK Push sent! Check your phone.');
    } catch (err: unknown) {
      const axiosErr = err as { response?: { data?: { detail?: string } } };
      setMpesaResult(axiosErr.response?.data?.detail || 'M-Pesa request failed. Check credentials.');
    } finally {
      setMpesaLoading(false);
    }
  };

  if (loading) return <div className="flex items-center justify-center min-h-96"><div className="animate-spin rounded-full h-8 w-8 border-b-2 border-green-700" /></div>;

  const completedPayments = payments.filter((p) => p.status === 'completed');
  const pendingPayments = payments.filter((p) => p.status === 'pending');

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between flex-wrap gap-2">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Payments</h1>
          <p className="text-gray-500 mt-1">{payments.length} total payments</p>
        </div>
        <div className="flex gap-2">
          {user?.role === 'tenant' && (
            <Button variant="outline" onClick={() => setMpesaDialog(true)}>
              <Smartphone className="h-4 w-4 mr-2" />Pay via M-Pesa
            </Button>
          )}
          {user?.role !== 'tenant' && (
            <Button onClick={() => { setForm({ lease_id: '', amount: 0, due_date: '', payment_method: 'mpesa', status: 'pending' }); setDialogOpen(true); }}>
              <Plus className="h-4 w-4 mr-2" />Record Payment
            </Button>
          )}
        </div>
      </div>

      <Tabs defaultValue="all">
        <TabsList>
          <TabsTrigger value="all">All ({payments.length})</TabsTrigger>
          <TabsTrigger value="pending">Pending ({pendingPayments.length})</TabsTrigger>
          <TabsTrigger value="completed">Completed ({completedPayments.length})</TabsTrigger>
        </TabsList>

        {['all', 'pending', 'completed'].map((tab) => (
          <TabsContent key={tab} value={tab}>
            <Card>
              <CardContent className="p-0">
                <Table>
                  <TableHeader>
                    <TableRow>
                      <TableHead>Tenant</TableHead>
                      <TableHead className="hidden md:table-cell">Unit</TableHead>
                      <TableHead>Amount (KES)</TableHead>
                      <TableHead className="hidden md:table-cell">Due Date</TableHead>
                      <TableHead>Method</TableHead>
                      <TableHead>Status</TableHead>
                    </TableRow>
                  </TableHeader>
                  <TableBody>
                    {(tab === 'all' ? payments : tab === 'pending' ? pendingPayments : completedPayments).map((p) => (
                      <TableRow key={p.id}>
                        <TableCell className="font-medium">{p.tenant_name || '-'}</TableCell>
                        <TableCell className="hidden md:table-cell">{p.unit_number || '-'}</TableCell>
                        <TableCell>{p.amount.toLocaleString()}</TableCell>
                        <TableCell className="hidden md:table-cell">{p.due_date ? new Date(p.due_date).toLocaleDateString() : '-'}</TableCell>
                        <TableCell className="capitalize">{(p.payment_method || '-').replace('_', ' ')}</TableCell>
                        <TableCell><Badge variant={statusColors[p.status]} className="capitalize">{p.status}</Badge></TableCell>
                      </TableRow>
                    ))}
                    {(tab === 'all' ? payments : tab === 'pending' ? pendingPayments : completedPayments).length === 0 && (
                      <TableRow><TableCell colSpan={6} className="text-center py-8 text-gray-500">No payments found</TableCell></TableRow>
                    )}
                  </TableBody>
                </Table>
              </CardContent>
            </Card>
          </TabsContent>
        ))}
      </Tabs>

      {/* Record Payment Dialog */}
      <Dialog open={dialogOpen} onOpenChange={setDialogOpen}>
        <DialogContent>
          <DialogHeader><DialogTitle>Record Payment</DialogTitle></DialogHeader>
          <div className="space-y-4">
            <div className="space-y-2">
              <Label>Lease</Label>
              <Select value={form.lease_id} onValueChange={(v) => setForm({ ...form, lease_id: v })}>
                <SelectTrigger><SelectValue placeholder="Select lease" /></SelectTrigger>
                <SelectContent>
                  {leases.map((l) => <SelectItem key={l.id} value={l.id}>{l.tenant_name} - {l.unit_number}</SelectItem>)}
                </SelectContent>
              </Select>
            </div>
            <div className="grid grid-cols-2 gap-4">
              <div className="space-y-2"><Label>Amount (KES)</Label><Input type="number" value={form.amount} onChange={(e) => setForm({ ...form, amount: Number(e.target.value) })} /></div>
              <div className="space-y-2"><Label>Due Date</Label><Input type="date" value={form.due_date} onChange={(e) => setForm({ ...form, due_date: e.target.value })} /></div>
            </div>
            <div className="grid grid-cols-2 gap-4">
              <div className="space-y-2">
                <Label>Method</Label>
                <Select value={form.payment_method} onValueChange={(v) => setForm({ ...form, payment_method: v })}>
                  <SelectTrigger><SelectValue /></SelectTrigger>
                  <SelectContent>
                    <SelectItem value="mpesa">M-Pesa</SelectItem>
                    <SelectItem value="bank_transfer">Bank Transfer</SelectItem>
                    <SelectItem value="cash">Cash</SelectItem>
                    <SelectItem value="cheque">Cheque</SelectItem>
                  </SelectContent>
                </Select>
              </div>
              <div className="space-y-2">
                <Label>Status</Label>
                <Select value={form.status} onValueChange={(v) => setForm({ ...form, status: v })}>
                  <SelectTrigger><SelectValue /></SelectTrigger>
                  <SelectContent>
                    <SelectItem value="pending">Pending</SelectItem>
                    <SelectItem value="completed">Completed</SelectItem>
                  </SelectContent>
                </Select>
              </div>
            </div>
          </div>
          <DialogFooter>
            <Button variant="outline" onClick={() => setDialogOpen(false)}>Cancel</Button>
            <Button onClick={handleSubmit}>Record</Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* M-Pesa Dialog */}
      <Dialog open={mpesaDialog} onOpenChange={setMpesaDialog}>
        <DialogContent>
          <DialogHeader><DialogTitle className="flex items-center gap-2"><Smartphone className="h-5 w-5 text-green-600" />Pay via M-Pesa (Lipa Na M-Pesa)</DialogTitle></DialogHeader>
          <div className="space-y-4">
            <div className="space-y-2">
              <Label>Lease</Label>
              <Select value={mpesaForm.lease_id} onValueChange={(v) => setMpesaForm({ ...mpesaForm, lease_id: v })}>
                <SelectTrigger><SelectValue placeholder="Select lease" /></SelectTrigger>
                <SelectContent>
                  {leases.filter((l) => l.status === 'active').map((l) => (
                    <SelectItem key={l.id} value={l.id}>{l.unit_number} - KES {l.rent_amount.toLocaleString()}</SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
            <div className="space-y-2"><Label>Phone Number (254...)</Label><Input value={mpesaForm.phone} onChange={(e) => setMpesaForm({ ...mpesaForm, phone: e.target.value })} placeholder="254700000000" /></div>
            <div className="space-y-2"><Label>Amount (KES)</Label><Input type="number" value={mpesaForm.amount} onChange={(e) => setMpesaForm({ ...mpesaForm, amount: Number(e.target.value) })} /></div>
            {mpesaResult && (
              <div className={`p-3 rounded-md text-sm ${mpesaResult.includes('fail') || mpesaResult.includes('error') ? 'bg-red-50 text-red-700' : 'bg-green-50 text-green-700'}`}>
                {mpesaResult}
              </div>
            )}
          </div>
          <DialogFooter>
            <Button variant="outline" onClick={() => setMpesaDialog(false)}>Cancel</Button>
            <Button onClick={handleMpesa} disabled={mpesaLoading}>
              <CreditCard className="h-4 w-4 mr-2" />{mpesaLoading ? 'Processing...' : 'Send STK Push'}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
}
