import { getSessionInfo } from '@/lib/authz';
import { redirect } from 'next/navigation';
import CustomersClient from './CustomersClient';
import '../../demo/demo.css';

export const dynamic = 'force-dynamic';

export default async function CustomersPage() {
  const { user, isOwner } = await getSessionInfo();
  if (!user) redirect('/login');
  if (!isOwner) redirect('/demo');
  return <CustomersClient />;
}
