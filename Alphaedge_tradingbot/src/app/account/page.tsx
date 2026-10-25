import { getSessionInfo } from '@/lib/authz';
import { redirect } from 'next/navigation';
import AccountClient from './AccountClient';
import '../demo/demo.css';

export const dynamic = 'force-dynamic';

// Customer self-service: any signed-in user whose email matches an onboarded
// customer sees their own account. No viewer approval is needed, because the
// data shown is the customer's own.
export default async function AccountPage() {
  const { user } = await getSessionInfo();
  if (!user) redirect('/login');
  return <AccountClient />;
}
