/**
 * Import page for Finanzguru transactions.
 */
'use client';

import { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { ImportWizard } from '@/components/features/transactions/ImportWizard';

export default function ImportPage() {
  const router = useRouter();
  const [token, setToken] = useState<string | null>(null);

  useEffect(() => {
    // Get token from localStorage or cookies
    const storedToken = localStorage.getItem('token');
    if (!storedToken) {
      router.push('/login');
      return;
    }
    setToken(storedToken);
  }, [router]);

  if (!token) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <p>Loading...</p>
      </div>
    );
  }

  return (
    <div className="container mx-auto py-8">
      <ImportWizard
        token={token}
        onImportComplete={(result) => {
          if (result.imported > 0) {
            // Redirect to transactions page after successful import
            setTimeout(() => {
              router.push('/transactions');
            }, 2000);
          }
        }}
      />
    </div>
  );
}
