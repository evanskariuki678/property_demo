import { useEffect, useState } from 'react';
import { getTenants } from '@/services/api';
import { User } from '@/types';
import { Card, CardContent } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table';
import { Users } from 'lucide-react';

export default function Tenants() {
  const [tenants, setTenants] = useState<User[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    getTenants()
      .then((r) => setTenants(Array.isArray(r.data) ? r.data : []))
      .catch(console.error)
      .finally(() => setLoading(false));
  }, []);

  if (loading) return <div className="flex items-center justify-center min-h-96"><div className="animate-spin rounded-full h-8 w-8 border-b-2 border-green-700" /></div>;

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-gray-900">Tenants</h1>
        <p className="text-gray-500 mt-1">{tenants.length} registered tenants</p>
      </div>

      {tenants.length === 0 ? (
        <Card><CardContent className="p-12 text-center text-gray-500">
          <Users className="h-12 w-12 mx-auto mb-4 text-gray-300" />
          <p>No tenants found.</p>
        </CardContent></Card>
      ) : (
        <Card>
          <CardContent className="p-0">
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>Name</TableHead>
                  <TableHead className="hidden md:table-cell">Email</TableHead>
                  <TableHead>Phone</TableHead>
                  <TableHead className="hidden md:table-cell">ID Number</TableHead>
                  <TableHead>Status</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {tenants.map((t) => (
                  <TableRow key={t.id}>
                    <TableCell className="font-medium">{t.full_name}</TableCell>
                    <TableCell className="hidden md:table-cell">{t.email}</TableCell>
                    <TableCell>{t.phone}</TableCell>
                    <TableCell className="hidden md:table-cell">{t.id_number || '-'}</TableCell>
                    <TableCell>
                      <Badge variant={t.is_active ? 'default' : 'destructive'}>
                        {t.is_active ? 'Active' : 'Inactive'}
                      </Badge>
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </CardContent>
        </Card>
      )}
    </div>
  );
}
