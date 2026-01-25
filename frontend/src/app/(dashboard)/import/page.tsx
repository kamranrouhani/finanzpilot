'use client';

import { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { DashboardLayout } from '@/components/layout/DashboardLayout';
import { ImportWizard } from '@/components/features/transactions/ImportWizard';

export default function ImportPage() {
  const router = useRouter();
  const [token, setToken] = useState<string | null>(null);

  useEffect(() => {
    const storedToken = localStorage.getItem('token');
    if (!storedToken) {
      router.push('/login');
      return;
    }
    setToken(storedToken);
  }, [router]);

  if (!token) {
    return (
      <DashboardLayout>
        <div className="flex items-center justify-center min-h-[400px]">
          <div className="text-center">
            <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto"></div>
            <p className="mt-4 text-slate-600">Loading...</p>
          </div>
        </div>
      </DashboardLayout>
    );
  }

  return (
    <DashboardLayout>
      <div className="space-y-6">
        <div>
          <h1 className="text-3xl font-bold text-slate-900">Import Transactions</h1>
          <p className="text-slate-600 mt-2">Upload your Finanzguru export file</p>
        </div>

        <ImportWizard
          token={token}
          onImportComplete={(result) => {
            if (result.imported > 0) {
              setTimeout(() => {
                router.push('/transactions');
              }, 2000);
            }
          }}
        />
      </div>
    </DashboardLayout>
  );
}
