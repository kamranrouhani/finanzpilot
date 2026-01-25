"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { DashboardLayout } from "@/components/layout/DashboardLayout";
import { getTransactionStats, type TransactionStats } from "@/lib/api/transactions";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { ArrowUp, ArrowDown, Wallet, TrendingUp, Upload, CreditCard, Receipt, Target } from "lucide-react";

export default function DashboardPage() {
  const router = useRouter();
  const [stats, setStats] = useState<TransactionStats | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const fetchStats = async () => {
      const token = localStorage.getItem("token");
      if (!token) {
        router.push("/login");
        return;
      }

      try {
        const data = await getTransactionStats(token);
        setStats(data);
      } catch (err) {
        console.error("Failed to fetch stats:", err);
        setError("Failed to load statistics");
      } finally {
        setLoading(false);
      }
    };

    fetchStats();
  }, [router]);

  const formatCurrency = (amount: number) => {
    return new Intl.NumberFormat('de-DE', {
      style: 'currency',
      currency: 'EUR',
    }).format(amount);
  };

  if (loading) {
    return (
      <DashboardLayout>
        <div className="flex items-center justify-center min-h-[400px]">
          <div className="text-center">
            <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto"></div>
            <p className="mt-4 text-slate-600">Loading dashboard...</p>
          </div>
        </div>
      </DashboardLayout>
    );
  }

  const hasTransactions = stats && stats.transaction_count > 0;

  return (
    <DashboardLayout>
      <div className="space-y-8">
        {/* Header */}
        <div>
          <h1 className="text-3xl font-bold text-slate-900">Dashboard</h1>
          <p className="text-slate-600 mt-2">Overview of your financial activity</p>
        </div>

        {error && (
          <div className="p-4 bg-red-50 border border-red-200 rounded-lg">
            <p className="text-sm text-red-600">{error}</p>
          </div>
        )}

        {!hasTransactions ? (
          <Card>
            <CardHeader>
              <CardTitle>Welcome to FinanzPilot!</CardTitle>
              <CardDescription>
                Get started by importing your transactions from Finanzguru
              </CardDescription>
            </CardHeader>
            <CardContent>
              <Button onClick={() => router.push('/import')} className="gap-2">
                <Upload className="h-4 w-4" />
                Import Transactions
              </Button>
            </CardContent>
          </Card>
        ) : (
          <>
            {/* Stats Cards */}
            <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
              <Card>
                <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                  <CardTitle className="text-sm font-medium">Total Income</CardTitle>
                  <ArrowUp className="h-4 w-4 text-green-600" />
                </CardHeader>
                <CardContent>
                  <div className="text-2xl font-bold text-green-600">
                    {formatCurrency(stats!.total_income)}
                  </div>
                  <p className="text-xs text-slate-500 mt-1">This period</p>
                </CardContent>
              </Card>

              <Card>
                <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                  <CardTitle className="text-sm font-medium">Total Expenses</CardTitle>
                  <ArrowDown className="h-4 w-4 text-red-600" />
                </CardHeader>
                <CardContent>
                  <div className="text-2xl font-bold text-red-600">
                    {formatCurrency(stats!.total_expenses)}
                  </div>
                  <p className="text-xs text-slate-500 mt-1">This period</p>
                </CardContent>
              </Card>

              <Card>
                <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                  <CardTitle className="text-sm font-medium">Balance</CardTitle>
                  <Wallet className="h-4 w-4 text-blue-600" />
                </CardHeader>
                <CardContent>
                  <div className={`text-2xl font-bold ${stats!.balance >= 0 ? 'text-green-600' : 'text-red-600'}`}>
                    {formatCurrency(stats!.balance)}
                  </div>
                  <p className="text-xs text-slate-500 mt-1">Income - Expenses</p>
                </CardContent>
              </Card>

              <Card>
                <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                  <CardTitle className="text-sm font-medium">Transactions</CardTitle>
                  <TrendingUp className="h-4 w-4 text-slate-600" />
                </CardHeader>
                <CardContent>
                  <div className="text-2xl font-bold text-slate-900">
                    {stats!.transaction_count}
                  </div>
                  <p className="text-xs text-slate-500 mt-1">Total recorded</p>
                </CardContent>
              </Card>
            </div>

            {/* Quick Actions */}
            <div>
              <h2 className="text-xl font-semibold text-slate-900 mb-4">Quick Actions</h2>
              <div className="grid gap-4 md:grid-cols-3">
                <Card className="hover:shadow-lg transition-shadow cursor-pointer" onClick={() => router.push('/transactions')}>
                  <CardHeader>
                    <CardTitle className="flex items-center gap-2">
                      <CreditCard className="h-5 w-5 text-blue-600" />
                      Transactions
                    </CardTitle>
                    <CardDescription>
                      View and manage your financial transactions
                    </CardDescription>
                  </CardHeader>
                </Card>

                <Card className="hover:shadow-lg transition-shadow cursor-pointer" onClick={() => router.push('/budgets')}>
                  <CardHeader>
                    <CardTitle className="flex items-center gap-2">
                      <Target className="h-5 w-5 text-green-600" />
                      Budgets
                    </CardTitle>
                    <CardDescription>
                      Track spending against your budget goals
                    </CardDescription>
                  </CardHeader>
                </Card>

                <Card className="hover:shadow-lg transition-shadow cursor-pointer" onClick={() => router.push('/import')}>
                  <CardHeader>
                    <CardTitle className="flex items-center gap-2">
                      <Upload className="h-5 w-5 text-purple-600" />
                      Import Data
                    </CardTitle>
                    <CardDescription>
                      Import from Finanzguru XLSX/CSV files
                    </CardDescription>
                  </CardHeader>
                </Card>
              </div>
            </div>
          </>
        )}
      </div>
    </DashboardLayout>
  );
}
