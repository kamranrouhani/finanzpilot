/**
 * Dashboard navigation component.
 */
'use client';

import { useRouter } from 'next/navigation';
import { Button } from '@/components/ui/button';

interface DashboardNavProps {
  username?: string;
}

export default function DashboardNav({ username }: DashboardNavProps) {
  const router = useRouter();

  const handleLogout = () => {
    localStorage.removeItem('token');
    router.push('/login');
  };

  return (
    <nav className="bg-white shadow-sm border-b">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex justify-between items-center h-16">
          <h1
            className="text-2xl font-bold text-blue-600 cursor-pointer"
            onClick={() => router.push('/dashboard')}
          >
            FinanzPilot
          </h1>
          <div className="flex items-center gap-4">
            <Button
              variant="outline"
              size="sm"
              onClick={() => router.push('/dashboard')}
            >
              Dashboard
            </Button>
            <Button
              variant="outline"
              size="sm"
              onClick={() => router.push('/transactions')}
            >
              Transactions
            </Button>
            <Button
              variant="outline"
              size="sm"
              onClick={() => router.push('/budgets')}
            >
              Budgets
            </Button>
            <Button
              variant="outline"
              size="sm"
              onClick={() => router.push('/import')}
            >
              Import
            </Button>
            {username && (
              <span className="text-sm text-slate-600">{username}</span>
            )}
            <Button variant="outline" size="sm" onClick={handleLogout}>
              Logout
            </Button>
          </div>
        </div>
      </div>
    </nav>
  );
}
