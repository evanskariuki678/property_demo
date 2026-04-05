import { useEffect, useState } from 'react';
import { getUnits, getProperties, createUnit, updateUnit, deleteUnit } from '@/services/api';
import { Unit, Property } from '@/types';
import { useAuth } from '@/contexts/AuthContext';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Badge } from '@/components/ui/badge';
import { Card, CardContent } from '@/components/ui/card';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table';
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogFooter } from '@/components/ui/dialog';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Plus, Edit, Trash2, DoorOpen } from 'lucide-react';

const statusColors: Record<string, 'default' | 'warning' | 'destructive' | 'info'> = {
  vacant: 'default', occupied: 'info', maintenance: 'warning', reserved: 'secondary' as 'info',
};

export default function Units() {
  const { user } = useAuth();
  const [units, setUnits] = useState<Unit[]>([]);
  const [properties, setProperties] = useState<Property[]>([]);
  const [loading, setLoading] = useState(true);
  const [dialogOpen, setDialogOpen] = useState(false);
  const [editing, setEditing] = useState<Unit | null>(null);
  const [form, setForm] = useState({
    property_id: '', unit_number: '', unit_type: 'apartment', bedrooms: 1, bathrooms: 1,
    rent_amount: 0, deposit_amount: 0, status: 'vacant', floor_number: 0, area_sqft: 0, amenities: '',
  });

  const load = () => {
    Promise.all([getUnits(), getProperties()])
      .then(([u, p]) => { setUnits(u.data); setProperties(p.data); })
      .catch(console.error).finally(() => setLoading(false));
  };

  useEffect(load, []);

  const openCreate = () => {
    setEditing(null);
    setForm({
      property_id: properties[0]?.id || '', unit_number: '', unit_type: 'apartment', bedrooms: 1,
      bathrooms: 1, rent_amount: 0, deposit_amount: 0, status: 'vacant', floor_number: 0, area_sqft: 0, amenities: '',
    });
    setDialogOpen(true);
  };

  const openEdit = (u: Unit) => {
    setEditing(u);
    setForm({
      property_id: u.property_id, unit_number: u.unit_number, unit_type: u.unit_type,
      bedrooms: u.bedrooms, bathrooms: u.bathrooms, rent_amount: u.rent_amount,
      deposit_amount: u.deposit_amount, status: u.status, floor_number: u.floor_number || 0,
      area_sqft: u.area_sqft || 0, amenities: u.amenities || '',
    });
    setDialogOpen(true);
  };

  const handleSubmit = async () => {
    try {
      if (editing) await updateUnit(editing.id, form);
      else await createUnit(form);
      setDialogOpen(false);
      load();
    } catch (err) { console.error(err); }
  };

  const handleDelete = async (id: string) => {
    if (!confirm('Delete this unit?')) return;
    await deleteUnit(id);
    load();
  };

  if (loading) return <div className="flex items-center justify-center min-h-96"><div className="animate-spin rounded-full h-8 w-8 border-b-2 border-green-700" /></div>;

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Units</h1>
          <p className="text-gray-500 mt-1">{units.length} units across all properties</p>
        </div>
        {user?.role !== 'tenant' && (
          <Button onClick={openCreate}><Plus className="h-4 w-4 mr-2" />Add Unit</Button>
        )}
      </div>

      {units.length === 0 ? (
        <Card><CardContent className="p-12 text-center text-gray-500">
          <DoorOpen className="h-12 w-12 mx-auto mb-4 text-gray-300" />
          <p>No units yet. Add your first unit to get started.</p>
        </CardContent></Card>
      ) : (
        <Card>
          <CardContent className="p-0">
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>Unit</TableHead>
                  <TableHead className="hidden md:table-cell">Property</TableHead>
                  <TableHead>Type</TableHead>
                  <TableHead className="hidden md:table-cell">Bed/Bath</TableHead>
                  <TableHead>Rent (KES)</TableHead>
                  <TableHead>Status</TableHead>
                  {user?.role !== 'tenant' && <TableHead>Actions</TableHead>}
                </TableRow>
              </TableHeader>
              <TableBody>
                {units.map((u) => (
                  <TableRow key={u.id}>
                    <TableCell className="font-medium">{u.unit_number}</TableCell>
                    <TableCell className="hidden md:table-cell">{u.property_name || '-'}</TableCell>
                    <TableCell className="capitalize">{u.unit_type}</TableCell>
                    <TableCell className="hidden md:table-cell">{u.bedrooms}B/{u.bathrooms}Ba</TableCell>
                    <TableCell>{u.rent_amount.toLocaleString()}</TableCell>
                    <TableCell><Badge variant={statusColors[u.status] || 'secondary'} className="capitalize">{u.status}</Badge></TableCell>
                    {user?.role !== 'tenant' && (
                      <TableCell>
                        <div className="flex gap-1">
                          <Button variant="ghost" size="icon" onClick={() => openEdit(u)}><Edit className="h-4 w-4" /></Button>
                          <Button variant="ghost" size="icon" className="text-red-600" onClick={() => handleDelete(u.id)}><Trash2 className="h-4 w-4" /></Button>
                        </div>
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
          <DialogHeader><DialogTitle>{editing ? 'Edit Unit' : 'Add Unit'}</DialogTitle></DialogHeader>
          <div className="space-y-4 max-h-96 overflow-y-auto pr-2">
            <div className="space-y-2">
              <Label>Property</Label>
              <Select value={form.property_id} onValueChange={(v) => setForm({ ...form, property_id: v })}>
                <SelectTrigger><SelectValue placeholder="Select property" /></SelectTrigger>
                <SelectContent>
                  {properties.map((p) => <SelectItem key={p.id} value={p.id}>{p.name}</SelectItem>)}
                </SelectContent>
              </Select>
            </div>
            <div className="grid grid-cols-2 gap-4">
              <div className="space-y-2">
                <Label>Unit Number</Label>
                <Input value={form.unit_number} onChange={(e) => setForm({ ...form, unit_number: e.target.value })} />
              </div>
              <div className="space-y-2">
                <Label>Type</Label>
                <Select value={form.unit_type} onValueChange={(v) => setForm({ ...form, unit_type: v })}>
                  <SelectTrigger><SelectValue /></SelectTrigger>
                  <SelectContent>
                    <SelectItem value="apartment">Apartment</SelectItem>
                    <SelectItem value="studio">Studio</SelectItem>
                    <SelectItem value="bedsitter">Bedsitter</SelectItem>
                    <SelectItem value="shop">Shop</SelectItem>
                    <SelectItem value="office">Office</SelectItem>
                  </SelectContent>
                </Select>
              </div>
            </div>
            <div className="grid grid-cols-2 gap-4">
              <div className="space-y-2"><Label>Bedrooms</Label><Input type="number" value={form.bedrooms} onChange={(e) => setForm({ ...form, bedrooms: Number(e.target.value) })} /></div>
              <div className="space-y-2"><Label>Bathrooms</Label><Input type="number" value={form.bathrooms} onChange={(e) => setForm({ ...form, bathrooms: Number(e.target.value) })} /></div>
            </div>
            <div className="grid grid-cols-2 gap-4">
              <div className="space-y-2"><Label>Rent (KES)</Label><Input type="number" value={form.rent_amount} onChange={(e) => setForm({ ...form, rent_amount: Number(e.target.value) })} /></div>
              <div className="space-y-2"><Label>Deposit (KES)</Label><Input type="number" value={form.deposit_amount} onChange={(e) => setForm({ ...form, deposit_amount: Number(e.target.value) })} /></div>
            </div>
            <div className="space-y-2">
              <Label>Status</Label>
              <Select value={form.status} onValueChange={(v) => setForm({ ...form, status: v })}>
                <SelectTrigger><SelectValue /></SelectTrigger>
                <SelectContent>
                  <SelectItem value="vacant">Vacant</SelectItem>
                  <SelectItem value="occupied">Occupied</SelectItem>
                  <SelectItem value="maintenance">Maintenance</SelectItem>
                  <SelectItem value="reserved">Reserved</SelectItem>
                </SelectContent>
              </Select>
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
