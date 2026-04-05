import { useEffect, useState } from 'react';
import { getMaintenanceRequests, createMaintenanceRequest, updateMaintenanceRequest, getUnits } from '@/services/api';
import { MaintenanceRequest, Unit } from '@/types';
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
import { Plus, Edit, Wrench } from 'lucide-react';

const priorityColors: Record<string, 'default' | 'warning' | 'destructive' | 'info'> = {
  low: 'default', medium: 'info', high: 'warning', urgent: 'destructive',
};
const statusColors: Record<string, 'default' | 'warning' | 'destructive' | 'info'> = {
  open: 'warning', in_progress: 'info', completed: 'default', cancelled: 'destructive',
};

export default function Maintenance() {
  const { user } = useAuth();
  const [requests, setRequests] = useState<MaintenanceRequest[]>([]);
  const [units, setUnits] = useState<Unit[]>([]);
  const [loading, setLoading] = useState(true);
  const [dialogOpen, setDialogOpen] = useState(false);
  const [editing, setEditing] = useState<MaintenanceRequest | null>(null);
  const [form, setForm] = useState({
    unit_id: '', title: '', description: '', priority: 'medium', status: 'open', resolution_notes: '',
  });

  const load = () => {
    Promise.all([getMaintenanceRequests(), getUnits()])
      .then(([m, u]) => { setRequests(m.data); setUnits(u.data); })
      .catch(console.error).finally(() => setLoading(false));
  };

  useEffect(load, []);

  const openCreate = () => {
    setEditing(null);
    setForm({ unit_id: '', title: '', description: '', priority: 'medium', status: 'open', resolution_notes: '' });
    setDialogOpen(true);
  };

  const openEdit = (m: MaintenanceRequest) => {
    setEditing(m);
    setForm({
      unit_id: m.unit_id, title: m.title, description: m.description,
      priority: m.priority, status: m.status, resolution_notes: m.resolution_notes || '',
    });
    setDialogOpen(true);
  };

  const handleSubmit = async () => {
    try {
      if (editing) await updateMaintenanceRequest(editing.id, form);
      else await createMaintenanceRequest(form);
      setDialogOpen(false);
      load();
    } catch (err) { console.error(err); }
  };

  if (loading) return <div className="flex items-center justify-center min-h-96"><div className="animate-spin rounded-full h-8 w-8 border-b-2 border-green-700" /></div>;

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Maintenance Requests</h1>
          <p className="text-gray-500 mt-1">{requests.length} requests</p>
        </div>
        <Button onClick={openCreate}><Plus className="h-4 w-4 mr-2" />New Request</Button>
      </div>

      {requests.length === 0 ? (
        <Card><CardContent className="p-12 text-center text-gray-500">
          <Wrench className="h-12 w-12 mx-auto mb-4 text-gray-300" />
          <p>No maintenance requests.</p>
        </CardContent></Card>
      ) : (
        <Card>
          <CardContent className="p-0">
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>Title</TableHead>
                  <TableHead className="hidden md:table-cell">Unit</TableHead>
                  <TableHead className="hidden md:table-cell">Submitted By</TableHead>
                  <TableHead>Priority</TableHead>
                  <TableHead>Status</TableHead>
                  <TableHead>Actions</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {requests.map((m) => (
                  <TableRow key={m.id}>
                    <TableCell className="font-medium">{m.title}</TableCell>
                    <TableCell className="hidden md:table-cell">{m.unit_number || '-'}</TableCell>
                    <TableCell className="hidden md:table-cell">{m.submitter_name || '-'}</TableCell>
                    <TableCell><Badge variant={priorityColors[m.priority]} className="capitalize">{m.priority}</Badge></TableCell>
                    <TableCell><Badge variant={statusColors[m.status]} className="capitalize">{m.status.replace('_', ' ')}</Badge></TableCell>
                    <TableCell>
                      <Button variant="ghost" size="icon" onClick={() => openEdit(m)}><Edit className="h-4 w-4" /></Button>
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </CardContent>
        </Card>
      )}

      <Dialog open={dialogOpen} onOpenChange={setDialogOpen}>
        <DialogContent>
          <DialogHeader><DialogTitle>{editing ? 'Update Request' : 'New Maintenance Request'}</DialogTitle></DialogHeader>
          <div className="space-y-4">
            <div className="space-y-2">
              <Label>Unit</Label>
              <Select value={form.unit_id} onValueChange={(v) => setForm({ ...form, unit_id: v })}>
                <SelectTrigger><SelectValue placeholder="Select unit" /></SelectTrigger>
                <SelectContent>
                  {units.map((u) => <SelectItem key={u.id} value={u.id}>{u.unit_number} - {u.property_name}</SelectItem>)}
                </SelectContent>
              </Select>
            </div>
            <div className="space-y-2">
              <Label>Title</Label>
              <Input value={form.title} onChange={(e) => setForm({ ...form, title: e.target.value })} placeholder="Brief description of the issue" />
            </div>
            <div className="space-y-2">
              <Label>Description</Label>
              <Textarea value={form.description} onChange={(e) => setForm({ ...form, description: e.target.value })} rows={3} placeholder="Detailed description..." />
            </div>
            <div className="grid grid-cols-2 gap-4">
              <div className="space-y-2">
                <Label>Priority</Label>
                <Select value={form.priority} onValueChange={(v) => setForm({ ...form, priority: v })}>
                  <SelectTrigger><SelectValue /></SelectTrigger>
                  <SelectContent>
                    <SelectItem value="low">Low</SelectItem>
                    <SelectItem value="medium">Medium</SelectItem>
                    <SelectItem value="high">High</SelectItem>
                    <SelectItem value="urgent">Urgent</SelectItem>
                  </SelectContent>
                </Select>
              </div>
              {editing && user?.role !== 'tenant' && (
                <div className="space-y-2">
                  <Label>Status</Label>
                  <Select value={form.status} onValueChange={(v) => setForm({ ...form, status: v })}>
                    <SelectTrigger><SelectValue /></SelectTrigger>
                    <SelectContent>
                      <SelectItem value="open">Open</SelectItem>
                      <SelectItem value="in_progress">In Progress</SelectItem>
                      <SelectItem value="completed">Completed</SelectItem>
                      <SelectItem value="cancelled">Cancelled</SelectItem>
                    </SelectContent>
                  </Select>
                </div>
              )}
            </div>
            {editing && user?.role !== 'tenant' && (
              <div className="space-y-2">
                <Label>Resolution Notes</Label>
                <Textarea value={form.resolution_notes} onChange={(e) => setForm({ ...form, resolution_notes: e.target.value })} rows={2} />
              </div>
            )}
          </div>
          <DialogFooter>
            <Button variant="outline" onClick={() => setDialogOpen(false)}>Cancel</Button>
            <Button onClick={handleSubmit}>{editing ? 'Update' : 'Submit'}</Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
}
