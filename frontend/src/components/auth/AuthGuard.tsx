'use client';

import { useEffect, useState } from 'react';
import { useRouter } from 'next/navigation';

interface AuthGuardProps {
  children: React.ReactNode;
  requireAuth?: boolean;
}

export function AuthGuard({ children, requireAuth = true }: AuthGuardProps) {
  const router = useRouter();
  const [isChecking, setIsChecking] = useState(true);

  useEffect(() => {
    const token = localStorage.getItem('token');
    const hasToken = !!token;

    if (requireAuth && !hasToken) {
      // Protected route but no token - redirect to login
      router.push('/login');
    } else if (!requireAuth && hasToken) {
      // Auth page but already logged in - redirect to dashboard
      router.push('/dashboard');
    } else {
      setIsChecking(false);
    }
  }, [router, requireAuth]);

  if (isChecking) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto"></div>
          <p className="mt-4 text-slate-600">Loading...</p>
        </div>
      </div>
    );
  }

  return <>{children}</>;
}
