import { useEffect, useState } from 'react';
import { getDocuments, deleteDocument } from '@/services/api';
import { Document } from '@/types';
import { useAuth } from '@/contexts/AuthContext';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Card, CardContent } from '@/components/ui/card';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table';
import { Trash2, FolderOpen, FileText } from 'lucide-react';

export default function Documents() {
  const { user } = useAuth();
  const [documents, setDocuments] = useState<Document[]>([]);
  const [loading, setLoading] = useState(true);

  const load = () => {
    getDocuments().then((r) => setDocuments(r.data)).catch(console.error).finally(() => setLoading(false));
  };

  useEffect(load, []);

  const handleDelete = async (id: string) => {
    if (!confirm('Delete this document?')) return;
    await deleteDocument(id);
    load();
  };

  if (loading) return <div className="flex items-center justify-center min-h-96"><div className="animate-spin rounded-full h-8 w-8 border-b-2 border-green-700" /></div>;

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Documents</h1>
          <p className="text-gray-500 mt-1">{documents.length} documents</p>
        </div>
      </div>

      {documents.length === 0 ? (
        <Card><CardContent className="p-12 text-center text-gray-500">
          <FolderOpen className="h-12 w-12 mx-auto mb-4 text-gray-300" />
          <p>No documents uploaded yet.</p>
        </CardContent></Card>
      ) : (
        <Card>
          <CardContent className="p-0">
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>Name</TableHead>
                  <TableHead>Type</TableHead>
                  <TableHead className="hidden md:table-cell">Entity</TableHead>
                  <TableHead className="hidden md:table-cell">Uploaded By</TableHead>
                  <TableHead className="hidden md:table-cell">Date</TableHead>
                  {user?.role !== 'tenant' && <TableHead>Actions</TableHead>}
                </TableRow>
              </TableHeader>
              <TableBody>
                {documents.map((d) => (
                  <TableRow key={d.id}>
                    <TableCell className="font-medium">
                      <div className="flex items-center gap-2">
                        <FileText className="h-4 w-4 text-gray-400" />
                        {d.name}
                      </div>
                    </TableCell>
                    <TableCell><Badge variant="secondary" className="capitalize">{d.document_type}</Badge></TableCell>
                    <TableCell className="hidden md:table-cell capitalize">{d.entity_type}</TableCell>
                    <TableCell className="hidden md:table-cell">{d.uploader_name || '-'}</TableCell>
                    <TableCell className="hidden md:table-cell">{new Date(d.created_at).toLocaleDateString()}</TableCell>
                    {user?.role !== 'tenant' && (
                      <TableCell>
                        <Button variant="ghost" size="icon" className="text-red-600" onClick={() => handleDelete(d.id)}>
                          <Trash2 className="h-4 w-4" />
                        </Button>
                      </TableCell>
                    )}
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
