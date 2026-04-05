import { useEffect, useState } from 'react';
import { getLeases, createLease, updateLease, getUnits, getTenants } from '@/services/api';
import { Lease, Unit, User } from '@/types';
import { useAuth } from '@/contexts/AuthContext';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Badge } from '@/components/ui/badge';
import { Card, CardContent } from '@/components/ui/card';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table';
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogFooter } from '@/components/ui/dialog';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Textarea } from '@/components/ui/textarea';
import { Plus, Edit, FileText } from 'lucide-react';

const statusColors: Record<string, 'default' | 'warning' | 'destructive' | 'info'> = {
  active: 'default', pending: 'warning', expired: 'destructive', terminated: 'destructive',
};

export default function Leases() {
  const { user } = useAuth();
  const [leases, setLeases] = useState<Lease[]>([]);
  const [units, setUnits] = useState<Unit[]>([]);
  const [tenants, setTenants] = useState<User[]>([]);
  const [loading, setLoading] = useState(true);
  const [dialogOpen, setDialogOpen] = useState(false);
  const [editing, setEditing] = useState<Lease | null>(null);
  const [form, setForm] = useState({
    unit_id: '', tenant_id: '', start_date: '', end_date: '',
    rent_amount: 0, deposit_amount: 0, status: 'active', terms: '',
  });

  const load = () => {
    Promise.all([getLeases(), getUnits(), getTenants()])
      .then(([l, u, t]) => {
        setLeases(l.data);
        setUnits(u.data);
        setTenants(Array.isArray(t.data) ? t.data : []);
      })
      .catch(console.error).finally(() => setLoading(false));
  };

  useEffect(load, []);

  const openCreate = () => {
    setEditing(null);
    setForm({ unit_id: '', tenant_id: '', start_date: '', end_date: '', rent_amount: 0, deposit_amount: 0, status: 'active', terms: '' });
    setDialogOpen(true);
  };

  const openEdit = (l: Lease) => {
    setEditing(l);
    setForm({
      unit_id: l.unit_id, tenant_id: l.tenant_id, start_date: l.start_date.split('T')[0],
      end_date: l.end_date.split('T')[0], rent_amount: l.rent_amount, deposit_amount: l.deposit_amount,
      status: l.status, terms: l.terms || '',
    });
    setDialogOpen(true);
  };

  const handleSubmit = async () => {
    try {
      if (editing) await updateLease(editing.id, form);
      else await createLease(form);
      setDialogOpen(false);
      load();
    } catch (err) { console.error(err); }
  };

  if (loading) return <div className="flex items-center justify-center min-h-96"><div className="animate-spin rounded-full h-8 w-8 border-b-2 border-green-700" /></div>;

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Leases</h1>
          <p className="text-gray-500 mt-1">{leases.length} leases</p>
        </div>
        {user?.role !== 'tenant' && (
          <Button onClick={openCreate}><Plus className="h-4 w-4 mr-2" />New Lease</Button>
        )}
      </div>

      {leases.length === 0 ? (
        <Card><CardContent className="p-12 text-center text-gray-500">
          <FileText className="h-12 w-12 mx-auto mb-4 text-gray-300" />
          <p>No leases found.</p>
        </CardContent></Card>
      ) : (
        <Card>
          <CardContent className="p-0">
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>Tenant</TableHead>
                  <TableHead className="hidden md:table-cell">Unit</TableHead>
                  <TableHead className="hidden md:table-cell">Property</TableHead>
                  <TableHead>Rent (KES)</TableHead>
                  <TableHead className="hidden md:table-cell">Period</TableHead>
                  <TableHead>Status</TableHead>
                  {user?.role !== 'tenant' && <TableHead>Actions</TableHead>}
                </TableRow>
              </TableHeader>
              <TableBody>
                {leases.map((l) => (
                  <TableRow key={l.id}>
                    <TableCell className="font-medium">{l.tenant_name || '-'}</TableCell>
                    <TableCell className="hidden md:table-cell">{l.unit_number || '-'}</TableCell>
                    <TableCell className="hidden md:table-cell">{l.property_name || '-'}</TableCell>
                    <TableCell>{l.rent_amount.toLocaleString()}</TableCell>
                    <TableCell className="hidden md:table-cell text-sm">
                      {new Date(l.start_date).toLocaleDateString()} - {new Date(l.end_date).toLocaleDateString()}
                    </TableCell>
                    <TableCell>
                      <Badge variant={statusColors[l.status]} className="capitalize">{l.status}</Badge>
                    </TableCell>
                    {user?.role !== 'tenant' && (
                      <TableCell>
                        <Button variant="ghost" size="icon" onClick={() => openEdit(l)}><Edit className="h-4 w-4" /></Button>
                      </TableCell>
                    )}
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </CardContent>
        </Card>
      )}

      <Dialog open={dialogOpen} onOpenChange={setDialogOpen}>
        <DialogContent className="max-w-lg">
          <DialogHeader><DialogTitle>{editing ? 'Edit Lease' : 'New Lease'}</DialogTitle></DialogHeader>
          <div className="space-y-4 max-h-96 overflow-y-auto pr-2">
            <div className="space-y-2">
              <Label>Unit</Label>
              <Select value={form.unit_id} onValueChange={(v) => setForm({ ...form, unit_id: v })}>
                <SelectTrigger><SelectValue placeholder="Select unit" /></SelectTrigger>
                <SelectContent>
                  {units.filter((u) => u.status === 'vacant' || u.id === editing?.unit_id).map((u) => (
                    <SelectItem key={u.id} value={u.id}>{u.unit_number} - {u.property_name}</SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
            <div className="space-y-2">
              <Label>Tenant</Label>
              <Select value={form.tenant_id} onValueChange={(v) => setForm({ ...form, tenant_id: v })}>
                <SelectTrigger><SelectValue placeholder="Select tenant" /></SelectTrigger>
                <SelectContent>
                  {tenants.map((t) => <SelectItem key={t.id} value={t.id}>{t.full_name} ({t.email})</SelectItem>)}
                </SelectContent>
              </Select>
            </div>
            <div className="grid grid-cols-2 gap-4">
              <div className="space-y-2"><Label>Start Date</Label><Input type="date" value={form.start_date} onChange={(e) => setForm({ ...form, start_date: e.target.value })} /></div>
              <div className="space-y-2"><Label>End Date</Label><Input type="date" value={form.end_date} onChange={(e) => setForm({ ...form, end_date: e.target.value })} /></div>
            </div>
            <div className="grid grid-cols-2 gap-4">
              <div className="space-y-2"><Label>Rent (KES)</Label><Input type="number" value={form.rent_amount} onChange={(e) => setForm({ ...form, rent_amount: Number(e.target.value) })} /></div>
              <div className="space-y-2"><Label>Deposit (KES)</Label><Input type="number" value={form.deposit_amount} onChange={(e) => setForm({ ...form, deposit_amount: Number(e.target.value) })} /></div>
            </div>
            {editing && (
              <div className="space-y-2">
                <Label>Status</Label>
                <Select value={form.status} onValueChange={(v) => setForm({ ...form, status: v })}>
                  <SelectTrigger><SelectValue /></SelectTrigger>
                  <SelectContent>
                    <SelectItem value="active">Active</SelectItem>
                    <SelectItem value="expired">Expired</SelectItem>
                    <SelectItem value="terminated">Terminated</SelectItem>
                    <SelectItem value="pending">Pending</SelectItem>
                  </SelectContent>
                </Select>
              </div>
            )}
            <div className="space-y-2">
              <Label>Terms & Conditions</Label>
              <Textarea value={form.terms} onChange={(e) => setForm({ ...form, terms: e.target.value })} rows={3} />
            </div>
          </div>
          <DialogFooter>
            <Button variant="outline" onClick={() => setDialogOpen(false)}>Cancel</Button>
            <Button onClick={handleSubmit}>{editing ? 'Update' : 'Create'}</Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
}
