import type {
  Budget,
  BudgetCreate,
  BudgetUpdate,
  BudgetSummary,
} from "@/types/budget";

const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

function getAuthHeaders(token: string): HeadersInit {
  return {
    "Content-Type": "application/json",
    Authorization: `Bearer ${token}`,
  };
}

export async function createBudget(
  data: BudgetCreate,
  token: string
): Promise<Budget> {
  const response = await fetch(`${API_URL}/api/budgets`, {
    method: "POST",
    headers: getAuthHeaders(token),
    body: JSON.stringify(data),
  });

  if (!response.ok) {
    const error = await response.json();
    throw new Error(error.detail || "Failed to create budget");
  }

  return response.json();
}

export async function getBudgets(token: string): Promise<Budget[]> {
  const response = await fetch(`${API_URL}/api/budgets`, {
    headers: getAuthHeaders(token),
  });

  if (!response.ok) {
    const error = await response.json();
    throw new Error(error.detail || "Failed to fetch budgets");
  }

  return response.json();
}

export async function getBudget(
  budgetId: string,
  token: string
): Promise<Budget> {
  const response = await fetch(`${API_URL}/api/budgets/${budgetId}`, {
    headers: getAuthHeaders(token),
  });

  if (!response.ok) {
    const error = await response.json();
    throw new Error(error.detail || "Failed to fetch budget");
  }

  return response.json();
}

export async function updateBudget(
  budgetId: string,
  data: BudgetUpdate,
  token: string
): Promise<Budget> {
  const response = await fetch(`${API_URL}/api/budgets/${budgetId}`, {
    method: "PUT",
    headers: getAuthHeaders(token),
    body: JSON.stringify(data),
  });

  if (!response.ok) {
    const error = await response.json();
    throw new Error(error.detail || "Failed to update budget");
  }

  return response.json();
}

export async function deleteBudget(
  budgetId: string,
  token: string
): Promise<void> {
  const response = await fetch(`${API_URL}/api/budgets/${budgetId}`, {
    method: "DELETE",
    headers: getAuthHeaders(token),
  });

  if (!response.ok) {
    const error = await response.json();
    throw new Error(error.detail || "Failed to delete budget");
  }
}

export async function getBudgetSummary(
  token: string
): Promise<BudgetSummary> {
  const response = await fetch(`${API_URL}/api/budgets/summary`, {
    headers: getAuthHeaders(token),
  });

  if (!response.ok) {
    const error = await response.json();
    throw new Error(error.detail || "Failed to fetch budget summary");
  }

  return response.json();
}
