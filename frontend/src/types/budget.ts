export interface Budget {
  id: string;
  user_id: string;
  category_id: string;
  amount: number;
  period: "monthly" | "weekly" | "yearly";
  start_date: string;
  end_date?: string;
  is_active: boolean;
  created_at: string;
  updated_at: string;
}

export interface BudgetCreate {
  category_id: string;
  amount: number;
  period: "monthly" | "weekly" | "yearly";
  start_date: string;
  end_date?: string;
  is_active?: boolean;
}

export interface BudgetUpdate {
  category_id?: string;
  amount?: number;
  period?: "monthly" | "weekly" | "yearly";
  start_date?: string;
  end_date?: string;
  is_active?: boolean;
}

export interface BudgetWithProgress extends Budget {
  spent: number;
  remaining: number;
  percentage: number;
  is_over_budget: boolean;
  category_name?: string;
  category_name_de?: string;
}

export interface BudgetSummary {
  total_budgeted: number;
  total_spent: number;
  total_remaining: number;
  budgets: BudgetWithProgress[];
  over_budget_count: number;
}
