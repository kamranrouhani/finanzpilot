/**
 * API client for transactions.
 */

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

export interface Transaction {
  id: string;
  user_id: string;
  account_name: string | null;
  account_iban_last4: string | null;
  date: string;
  amount: string;
  currency: string;
  balance_after: string | null;
  counterparty: string | null;
  counterparty_iban: string | null;
  description: string | null;
  e_ref: string | null;
  mandate_ref: string | null;
  creditor_id: string | null;
  category_id: string | null;
  subcategory_id: string | null;
  tax_category_id: string | null;
  fg_main_category: string | null;
  fg_subcategory: string | null;
  fg_contract_name: string | null;
  fg_contract_frequency: string | null;
  fg_contract_id: string | null;
  fg_is_transfer: boolean;
  fg_excluded_from_budget: boolean;
  fg_transaction_type: string | null;
  fg_analysis_amount: string | null;
  fg_week: string | null;
  fg_month: string | null;
  fg_quarter: string | null;
  fg_year: string | null;
  tags: string[] | null;
  notes: string | null;
  source: string;
  created_at: string;
  updated_at: string;
}

export interface TransactionListResponse {
  items: Transaction[];
  total: number;
  skip: number;
  limit: number;
}

export interface TransactionFilters {
  skip?: number;
  limit?: number;
  start_date?: string;
  end_date?: string;
  category_id?: string;
  search?: string;
}

export interface TransactionImportResponse {
  total_rows: number;
  imported: number;
  skipped: number;
  errors: number;
  error_details?: string[];
}

export interface TransactionStats {
  total_income: number;
  total_expenses: number;
  balance: number;
  transaction_count: number;
}

/**
 * Get list of transactions with filtering.
 */
export async function getTransactions(
  token: string,
  filters: TransactionFilters = {}
): Promise<TransactionListResponse> {
  const params = new URLSearchParams();

  if (filters.skip !== undefined) params.append('skip', filters.skip.toString());
  if (filters.limit !== undefined) params.append('limit', filters.limit.toString());
  if (filters.start_date) params.append('start_date', filters.start_date);
  if (filters.end_date) params.append('end_date', filters.end_date);
  if (filters.category_id) params.append('category_id', filters.category_id);
  if (filters.search) params.append('search', filters.search);

  const url = `${API_URL}/api/transactions${params.toString() ? '?' + params.toString() : ''}`;

  const response = await fetch(url, {
    headers: {
      'Authorization': `Bearer ${token}`,
      'Content-Type': 'application/json',
    },
  });

  if (!response.ok) {
    throw new Error('Failed to fetch transactions');
  }

  return response.json();
}

/**
 * Get a single transaction by ID.
 */
export async function getTransaction(
  token: string,
  transactionId: string
): Promise<Transaction> {
  const response = await fetch(`${API_URL}/api/transactions/${transactionId}`, {
    headers: {
      'Authorization': `Bearer ${token}`,
      'Content-Type': 'application/json',
    },
  });

  if (!response.ok) {
    throw new Error('Failed to fetch transaction');
  }

  return response.json();
}

/**
 * Update a transaction.
 */
export async function updateTransaction(
  token: string,
  transactionId: string,
  data: {
    category_id?: string | null;
    subcategory_id?: string | null;
    tax_category_id?: string | null;
    tags?: string[];
    notes?: string;
  }
): Promise<Transaction> {
  const response = await fetch(`${API_URL}/api/transactions/${transactionId}`, {
    method: 'PUT',
    headers: {
      'Authorization': `Bearer ${token}`,
      'Content-Type': 'application/json',
    },
    body: JSON.stringify(data),
  });

  if (!response.ok) {
    throw new Error('Failed to update transaction');
  }

  return response.json();
}

/**
 * Delete a transaction.
 */
export async function deleteTransaction(
  token: string,
  transactionId: string
): Promise<void> {
  const response = await fetch(`${API_URL}/api/transactions/${transactionId}`, {
    method: 'DELETE',
    headers: {
      'Authorization': `Bearer ${token}`,
    },
  });

  if (!response.ok) {
    throw new Error('Failed to delete transaction');
  }
}

/**
 * Import transactions from Finanzguru file.
 */
export async function importTransactions(
  token: string,
  file: File,
  skipDuplicates: boolean = true
): Promise<TransactionImportResponse> {
  const formData = new FormData();
  formData.append('file', file);

  const url = `${API_URL}/api/transactions/import?skip_duplicates=${skipDuplicates}`;

  const response = await fetch(url, {
    method: 'POST',
    headers: {
      'Authorization': `Bearer ${token}`,
    },
    body: formData,
  });

  if (!response.ok) {
    throw new Error('Failed to import transactions');
  }

  return response.json();
}

/**
 * Get transaction statistics.
 */
export async function getTransactionStats(
  token: string,
  startDate?: string,
  endDate?: string
): Promise<TransactionStats> {
  const params = new URLSearchParams();
  if (startDate) params.append('start_date', startDate);
  if (endDate) params.append('end_date', endDate);

  const url = `${API_URL}/api/transactions/stats/summary${params.toString() ? '?' + params.toString() : ''}`;

  const response = await fetch(url, {
    headers: {
      'Authorization': `Bearer ${token}`,
      'Content-Type': 'application/json',
    },
  });

  if (!response.ok) {
    throw new Error('Failed to fetch transaction stats');
  }

  return response.json();
}
