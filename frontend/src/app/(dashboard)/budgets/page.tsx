/**
 * Budgets page showing all budgets with progress tracking.
 */
'use client';

import { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { getBudgetSummary, deleteBudget } from '@/lib/api/budgets';
import type { BudgetSummary } from '@/types/budget';
import BudgetProgressCard from '@/components/features/budgets/BudgetProgressCard';
import CreateBudgetDialog from '@/components/features/budgets/CreateBudgetDialog';
import DashboardNav from '@/components/features/auth/DashboardNav';

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
    return null;
  }

  const formatCurrency = (amount: number) => {
    return new Intl.NumberFormat('de-DE', {
      style: 'currency',
      currency: 'EUR',
    }).format(amount);
  };

  return (
    <div className="min-h-screen bg-slate-50">
      <DashboardNav />
      <div className="container mx-auto py-8 px-4">
      <div className="mb-6 flex justify-between items-center">
        <h1 className="text-3xl font-bold">Budgets</h1>
        <button
          onClick={() => setShowCreateDialog(true)}
          className="bg-blue-600 text-white px-4 py-2 rounded-md hover:bg-blue-700"
        >
          Create Budget
        </button>
      </div>

      {error && (
        <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded mb-4">
          {error}
        </div>
      )}

      {loading ? (
        <div className="text-center py-12">
          <p>Loading budgets...</p>
        </div>
      ) : !summary || summary.budgets.length === 0 ? (
        <div className="text-center py-12 bg-gray-50 rounded-lg">
          <p className="text-gray-600 mb-4">No budgets created yet</p>
          <button
            onClick={() => setShowCreateDialog(true)}
            className="bg-blue-600 text-white px-6 py-2 rounded-md hover:bg-blue-700"
          >
            Create Your First Budget
          </button>
        </div>
      ) : (
        <>
          {/* Summary Cards */}
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-8">
            <div className="bg-white p-6 rounded-lg shadow">
              <h3 className="text-sm font-medium text-gray-500 mb-2">
                Total Budgeted
              </h3>
              <p className="text-2xl font-bold text-gray-900">
                {formatCurrency(summary.total_budgeted)}
              </p>
            </div>

            <div className="bg-white p-6 rounded-lg shadow">
              <h3 className="text-sm font-medium text-gray-500 mb-2">
                Total Spent
              </h3>
              <p className="text-2xl font-bold text-gray-900">
                {formatCurrency(summary.total_spent)}
              </p>
            </div>

            <div className="bg-white p-6 rounded-lg shadow">
              <h3 className="text-sm font-medium text-gray-500 mb-2">
                Remaining
              </h3>
              <p
                className={`text-2xl font-bold ${
                  summary.total_remaining >= 0
                    ? 'text-green-600'
                    : 'text-red-600'
                }`}
              >
                {formatCurrency(summary.total_remaining)}
              </p>
            </div>
          </div>

          {/* Over Budget Warning */}
          {summary.over_budget_count > 0 && (
            <div className="bg-yellow-50 border border-yellow-200 text-yellow-800 px-4 py-3 rounded mb-6">
              ⚠️ {summary.over_budget_count} budget
              {summary.over_budget_count > 1 ? 's are' : ' is'} over limit
            </div>
          )}

          {/* Budget List */}
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
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
    </div>
  );
}
