"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { getCurrentUser } from "@/lib/api/auth";
import { getTransactionStats, type TransactionStats } from "@/lib/api/transactions";
import { Button } from "@/components/ui/button";
import type { User } from "@/types/auth";

export default function DashboardPage() {
  const router = useRouter();
  const [user, setUser] = useState<User | null>(null);
  const [stats, setStats] = useState<TransactionStats | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const token = localStorage.getItem("token");
    if (!token) {
      router.push("/login");
      return;
    }

    Promise.all([
      getCurrentUser(token),
      getTransactionStats(token).catch(() => null)
    ])
      .then(([userData, statsData]) => {
        setUser(userData);
        setStats(statsData);
      })
      .catch(() => {
        localStorage.removeItem("token");
        router.push("/login");
      })
      .finally(() => setLoading(false));
  }, [router]);

  const handleLogout = () => {
    localStorage.removeItem("token");
    router.push("/login");
  };

  const formatCurrency = (amount: number) => {
    return new Intl.NumberFormat('de-DE', {
      style: 'currency',
      currency: 'EUR',
    }).format(amount);
  };

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <p>Loading...</p>
      </div>
    );
  }

  if (!user) {
    return null;
  }

  return (
    <div className="min-h-screen bg-slate-50">
      <nav className="bg-white shadow-sm border-b">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between items-center h-16">
            <h1 className="text-2xl font-bold text-blue-600">FinanzPilot</h1>
            <div className="flex items-center gap-4">
              <Button variant="outline" size="sm" onClick={() => router.push('/transactions')}>
                Transactions
              </Button>
              <Button variant="outline" size="sm" onClick={() => router.push('/import')}>
                Import
              </Button>
              <span className="text-sm text-slate-600">
                {user.username}
              </span>
              <Button variant="outline" size="sm" onClick={handleLogout}>
                Logout
              </Button>
            </div>
          </div>
        </div>
      </nav>

      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <h2 className="text-2xl font-bold mb-6">Dashboard</h2>

        {stats && stats.transaction_count > 0 ? (
          <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-8">
            <div className="bg-white rounded-lg shadow p-6">
              <h3 className="text-sm font-medium text-gray-500 uppercase">Total Income</h3>
              <p className="mt-2 text-2xl font-bold text-green-600">
                {formatCurrency(stats.total_income)}
              </p>
            </div>
            <div className="bg-white rounded-lg shadow p-6">
              <h3 className="text-sm font-medium text-gray-500 uppercase">Total Expenses</h3>
              <p className="mt-2 text-2xl font-bold text-red-600">
                {formatCurrency(stats.total_expenses)}
              </p>
            </div>
            <div className="bg-white rounded-lg shadow p-6">
              <h3 className="text-sm font-medium text-gray-500 uppercase">Balance</h3>
              <p className={`mt-2 text-2xl font-bold ${stats.balance >= 0 ? 'text-green-600' : 'text-red-600'}`}>
                {formatCurrency(stats.balance)}
              </p>
            </div>
            <div className="bg-white rounded-lg shadow p-6">
              <h3 className="text-sm font-medium text-gray-500 uppercase">Transactions</h3>
              <p className="mt-2 text-2xl font-bold text-blue-600">
                {stats.transaction_count}
              </p>
            </div>
          </div>
        ) : (
          <div className="bg-white rounded-lg shadow p-8 text-center">
            <h3 className="text-xl font-semibold mb-2">Welcome to FinanzPilot!</h3>
            <p className="text-gray-600 mb-6">
              Get started by importing your transactions from Finanzguru.
            </p>
            <Button onClick={() => router.push('/import')}>
              Import Transactions
            </Button>
          </div>
        )}

        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <div className="bg-white rounded-lg shadow p-6">
            <h3 className="font-medium text-gray-900 mb-2">Transactions</h3>
            <p className="text-sm text-gray-600 mb-4">
              View and manage your financial transactions
            </p>
            <Button variant="outline" size="sm" onClick={() => router.push('/transactions')}>
              View Transactions
            </Button>
          </div>
          <div className="bg-white rounded-lg shadow p-6">
            <h3 className="font-medium text-gray-900 mb-2">Import</h3>
            <p className="text-sm text-gray-600 mb-4">
              Import from Finanzguru XLSX/CSV
            </p>
            <Button variant="outline" size="sm" onClick={() => router.push('/import')}>
              Import Data
            </Button>
          </div>
          <div className="bg-white rounded-lg shadow p-6">
            <h3 className="font-medium text-gray-900 mb-2">Categories</h3>
            <p className="text-sm text-gray-600 mb-4">
              Manage transaction categories
            </p>
            <Button variant="outline" size="sm" disabled>
              Coming Soon
            </Button>
          </div>
        </div>
      </main>
    </div>
  );
}
