/**
 * Budget progress card component showing budget status and spending.
 */
import type { BudgetWithProgress } from '@/types/budget';

interface BudgetProgressCardProps {
  budget: BudgetWithProgress;
  onDelete: (budgetId: string) => void;
}

export default function BudgetProgressCard({
  budget,
  onDelete,
}: BudgetProgressCardProps) {
  const formatCurrency = (amount: number) => {
    return new Intl.NumberFormat('de-DE', {
      style: 'currency',
      currency: 'EUR',
    }).format(amount);
  };

  const getProgressColor = () => {
    if (budget.is_over_budget) return 'bg-red-500';
    if (budget.percentage > 80) return 'bg-yellow-500';
    return 'bg-green-500';
  };

  const getBackgroundColor = () => {
    if (budget.is_over_budget) return 'bg-red-50 border-red-200';
    if (budget.percentage > 80) return 'bg-yellow-50 border-yellow-200';
    return 'bg-white border-gray-200';
  };

  return (
    <div className={`p-6 rounded-lg shadow border ${getBackgroundColor()}`}>
      <div className="flex justify-between items-start mb-4">
        <div>
          <h3 className="text-lg font-semibold text-gray-900">
            {budget.category_name || 'Unknown Category'}
          </h3>
          {budget.category_name_de && (
            <p className="text-sm text-gray-500">{budget.category_name_de}</p>
          )}
        </div>
        <button
          onClick={() => onDelete(budget.id)}
          className="text-gray-400 hover:text-red-600"
          title="Delete budget"
        >
          <svg
            className="w-5 h-5"
            fill="none"
            stroke="currentColor"
            viewBox="0 0 24 24"
          >
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              strokeWidth={2}
              d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16"
            />
          </svg>
        </button>
      </div>

      {/* Period Badge */}
      <div className="mb-3">
        <span className="inline-block bg-blue-100 text-blue-800 text-xs font-medium px-2 py-1 rounded">
          {budget.period}
        </span>
      </div>

      {/* Budget Amount */}
      <div className="mb-4">
        <div className="flex justify-between text-sm mb-1">
          <span className="text-gray-600">Spent</span>
          <span className="font-medium">
            {formatCurrency(budget.spent)} / {formatCurrency(budget.amount)}
          </span>
        </div>

        {/* Progress Bar */}
        <div className="w-full bg-gray-200 rounded-full h-2.5">
          <div
            className={`h-2.5 rounded-full transition-all ${getProgressColor()}`}
            style={{ width: `${Math.min(budget.percentage, 100)}%` }}
          />
        </div>

        <div className="flex justify-between text-xs mt-1">
          <span className="text-gray-500">{budget.percentage.toFixed(1)}%</span>
          <span
            className={
              budget.remaining >= 0 ? 'text-green-600' : 'text-red-600'
            }
          >
            {formatCurrency(Math.abs(budget.remaining))} {budget.remaining >= 0 ? 'left' : 'over'}
          </span>
        </div>
      </div>

      {/* Status Messages */}
      {budget.is_over_budget && (
        <div className="mt-3 text-xs text-red-700 font-medium">
          ⚠️ Budget exceeded
        </div>
      )}
      {!budget.is_over_budget && budget.percentage > 80 && (
        <div className="mt-3 text-xs text-yellow-700 font-medium">
          ⚠️ Nearing budget limit
        </div>
      )}
    </div>
  );
}
