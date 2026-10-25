import { getSessionInfo } from '@/lib/authz';
import { redirect } from 'next/navigation';
import CustomerDetailClient from './CustomerDetailClient';
import '../../../demo/demo.css';

export const dynamic = 'force-dynamic';

export default async function CustomerDetailPage({ params }: { params: Promise<{ id: string }> }) {
  const { user, isOwner } = await getSessionInfo();
  if (!user) redirect('/login');
  if (!isOwner) redirect('/demo');
  const { id } = await params;
  return <CustomerDetailClient id={id} />;
}
