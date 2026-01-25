/**
 * Budgets page showing all budgets with progress tracking.
 */
'use client';

import { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { DashboardLayout } from '@/components/layout/DashboardLayout';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { PlusCircle, AlertTriangle } from 'lucide-react';
import { getBudgetSummary, deleteBudget } from '@/lib/api/budgets';
import type { BudgetSummary } from '@/types/budget';
import BudgetProgressCard from '@/components/features/budgets/BudgetProgressCard';
import CreateBudgetDialog from '@/components/features/budgets/CreateBudgetDialog';

export default function BudgetsPage() {
  const router = useRouter();
  const [token, setToken] = useState<string | null>(null);
  const [summary, setSummary] = useState<BudgetSummary | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [showCreateDialog, setShowCreateDialog] = useState(false);

  useEffect(() => {
    const storedToken = localStorage.getItem('token');
    if (!storedToken) {
      router.push('/login');
      return;
    }
    setToken(storedToken);
  }, [router]);

  const fetchSummary = async () => {
    if (!token) return;

    setLoading(true);
    try {
      const data = await getBudgetSummary(token);
      setSummary(data);
      setError(null);
    } catch (err) {
      // Provide user-friendly error messages
      let message = 'Unable to load budgets. Please try again.';
      if (err instanceof Error) {
        if (err.message.includes('401') || err.message.includes('Unauthorized')) {
          message = 'Your session has expired. Please log in again.';
          setTimeout(() => router.push('/login'), 2000);
        } else if (err.message.includes('Network') || err.message.includes('fetch')) {
          message = 'Network error. Please check your connection.';
        }
      }
      setError(message);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (!token) return;
    fetchSummary();
  }, [token]);

  const handleDeleteBudget = async (budgetId: string) => {
    if (!token) return;

    if (!confirm('Are you sure you want to delete this budget?')) {
      return;
    }

    try {
      await deleteBudget(budgetId, token);
      await fetchSummary(); // Refresh the list
    } catch (err) {
      let message = 'Failed to delete budget. Please try again.';
      if (err instanceof Error && err.message.includes('404')) {
        message = 'Budget not found. It may have already been deleted.';
      }
      setError(message);
    }
  };

  const handleCreateSuccess = () => {
    setShowCreateDialog(false);
    fetchSummary(); // Refresh the list
  };

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

  const formatCurrency = (amount: number) => {
    return new Intl.NumberFormat('de-DE', {
      style: 'currency',
      currency: 'EUR',
    }).format(amount);
  };

  return (
    <DashboardLayout>
      <div className="space-y-6">
        <div className="flex justify-between items-center">
          <div>
            <h1 className="text-3xl font-bold text-slate-900">Budgets</h1>
            <p className="text-slate-600 mt-2">Track spending against your budget goals</p>
          </div>
          <Button onClick={() => setShowCreateDialog(true)} className="gap-2">
            <PlusCircle className="h-4 w-4" />
            Create Budget
          </Button>
        </div>

        {error && (
          <div className="p-4 bg-red-50 border border-red-200 rounded-lg">
            <p className="text-sm text-red-600">{error}</p>
          </div>
        )}

        {loading ? (
          <div className="flex items-center justify-center min-h-[400px]">
            <div className="text-center">
              <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto"></div>
              <p className="mt-4 text-slate-600">Loading budgets...</p>
            </div>
          </div>
        ) : !summary || summary.budgets.length === 0 ? (
          <Card>
            <CardContent className="flex flex-col items-center justify-center py-12">
              <p className="text-slate-600 mb-4">No budgets created yet</p>
              <Button onClick={() => setShowCreateDialog(true)} className="gap-2">
                <PlusCircle className="h-4 w-4" />
                Create Your First Budget
              </Button>
            </CardContent>
          </Card>
        ) : (
          <>
            {/* Summary Cards */}
            <div className="grid gap-4 md:grid-cols-3">
              <Card>
                <CardHeader className="pb-2">
                  <CardDescription>Total Budgeted</CardDescription>
                </CardHeader>
                <CardContent>
                  <p className="text-2xl font-bold text-slate-900">
                    {formatCurrency(summary.total_budgeted)}
                  </p>
                </CardContent>
              </Card>

              <Card>
                <CardHeader className="pb-2">
                  <CardDescription>Total Spent</CardDescription>
                </CardHeader>
                <CardContent>
                  <p className="text-2xl font-bold text-slate-900">
                    {formatCurrency(summary.total_spent)}
                  </p>
                </CardContent>
              </Card>

              <Card>
                <CardHeader className="pb-2">
                  <CardDescription>Remaining</CardDescription>
                </CardHeader>
                <CardContent>
                  <p
                    className={`text-2xl font-bold ${
                      summary.total_remaining >= 0
                        ? 'text-green-600'
                        : 'text-red-600'
                    }`}
                  >
                    {formatCurrency(summary.total_remaining)}
                  </p>
                </CardContent>
              </Card>
            </div>

            {/* Over Budget Warning */}
            {summary.over_budget_count > 0 && (
              <div className="flex items-center gap-2 p-4 bg-yellow-50 border border-yellow-200 rounded-lg">
                <AlertTriangle className="h-5 w-5 text-yellow-600" />
                <p className="text-sm text-yellow-800">
                  {summary.over_budget_count} budget
                  {summary.over_budget_count > 1 ? 's are' : ' is'} over limit
                </p>
              </div>
            )}

            {/* Budget List */}
            <div className="grid gap-6 md:grid-cols-2 lg:grid-cols-3">
              {summary.budgets.map((budget) => (
                <BudgetProgressCard
                  key={budget.id}
                  budget={budget}
                  onDelete={handleDeleteBudget}
                />
              ))}
            </div>
          </>
        )}

        {/* Create Budget Dialog */}
        {showCreateDialog && token && (
          <CreateBudgetDialog
            token={token}
            onClose={() => setShowCreateDialog(false)}
            onSuccess={handleCreateSuccess}
          />
        )}
      </div>
    </DashboardLayout>
  );
}
