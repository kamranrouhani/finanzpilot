/**
 * API client for categories and tax categories.
 */

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

export interface Category {
  id: string;
  name: string;
  name_de: string | null;
  parent_id: string | null;
  is_income: boolean;
  icon: string | null;
  color: string | null;
  sort_order: number;
}

export interface TaxCategory {
  id: string;
  name: string;
  name_de: string;
  anlage: string | null;
  description: string | null;
  deductible_percent: number;
}

/**
 * Get all categories (hierarchical).
 */
export async function getCategories(token: string): Promise<Category[]> {
  const response = await fetch(`${API_URL}/api/categories`, {
    headers: {
      'Authorization': `Bearer ${token}`,
      'Content-Type': 'application/json',
    },
  });

  if (!response.ok) {
    throw new Error('Failed to fetch categories');
  }

  return response.json();
}

/**
 * Get all tax categories.
 */
export async function getTaxCategories(token: string): Promise<TaxCategory[]> {
  const response = await fetch(`${API_URL}/api/categories/tax`, {
    headers: {
      'Authorization': `Bearer ${token}`,
      'Content-Type': 'application/json',
    },
  });

  if (!response.ok) {
    throw new Error('Failed to fetch tax categories');
  }

  return response.json();
}

/**
 * Create a new custom category.
 */
export async function createCategory(
  token: string,
  data: {
    name: string;
    name_de?: string;
    parent_id?: string | null;
    is_income?: boolean;
    icon?: string;
    color?: string;
  }
): Promise<Category> {
  const response = await fetch(`${API_URL}/api/categories`, {
    method: 'POST',
    headers: {
      'Authorization': `Bearer ${token}`,
      'Content-Type': 'application/json',
    },
    body: JSON.stringify(data),
  });

  if (!response.ok) {
    throw new Error('Failed to create category');
  }

  return response.json();
}

/**
 * Update a category.
 */
export async function updateCategory(
  token: string,
  categoryId: string,
  data: {
    name?: string;
    name_de?: string;
    icon?: string;
    color?: string;
  }
): Promise<Category> {
  const response = await fetch(`${API_URL}/api/categories/${categoryId}`, {
    method: 'PUT',
    headers: {
      'Authorization': `Bearer ${token}`,
      'Content-Type': 'application/json',
    },
    body: JSON.stringify(data),
  });

  if (!response.ok) {
    throw new Error('Failed to update category');
  }

  return response.json();
}

/**
 * Delete a category.
 */
export async function deleteCategory(
  token: string,
  categoryId: string
): Promise<void> {
  const response = await fetch(`${API_URL}/api/categories/${categoryId}`, {
    method: 'DELETE',
    headers: {
      'Authorization': `Bearer ${token}`,
    },
  });

  if (!response.ok) {
    throw new Error('Failed to delete category');
  }
}
