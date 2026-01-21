---
paths:
  - "frontend/src/**/*.ts"
  - "frontend/src/**/*.tsx"
---

# TypeScript/Next.js Code Style

## Formatting
- Use Prettier (printWidth: 100, singleQuote: true)
- Use ESLint with Next.js config

## TypeScript
- Strict mode enabled
- No `any` types (use `unknown` if needed)
- Export types/interfaces from dedicated files

```typescript
// types/transaction.ts
export interface Transaction {
  id: string;
  date: string;
  amount: number;
  counterparty: string;
  category?: Category;
}

export type TransactionCreate = Omit<Transaction, 'id'>;
```

## Components

### Naming
- PascalCase for components: `TransactionTable.tsx`
- camelCase for utilities: `formatCurrency.ts`
- kebab-case for routes: `transactions/[id]/page.tsx`

### Structure
```typescript
// 1. Imports (external, internal, types, styles)
import { useState } from 'react';
import { Button } from '@/components/ui/button';
import type { Transaction } from '@/types';

// 2. Types (if component-specific)
interface TransactionRowProps {
  transaction: Transaction;
  onEdit: (id: string) => void;
}

// 3. Component
export function TransactionRow({ transaction, onEdit }: TransactionRowProps) {
  // hooks first
  const [isEditing, setIsEditing] = useState(false);
  
  // handlers
  const handleClick = () => {
    onEdit(transaction.id);
  };
  
  // render
  return (
    <tr onClick={handleClick}>
      {/* ... */}
    </tr>
  );
}
```

### Use Client/Server Components Appropriately
```typescript
// Server Component (default) - for data fetching
// app/(dashboard)/transactions/page.tsx
export default async function TransactionsPage() {
  const transactions = await getTransactions();
  return <TransactionList transactions={transactions} />;
}

// Client Component - for interactivity
// components/features/transactions/TransactionList.tsx
'use client';

export function TransactionList({ transactions }: Props) {
  const [filter, setFilter] = useState('');
  // ...
}
```

## Hooks

### Custom Hooks
```typescript
// lib/hooks/useTransactions.ts
export function useTransactions(filters?: TransactionFilters) {
  const [data, setData] = useState<Transaction[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<Error | null>(null);
  
  // ... fetch logic
  
  return { data, isLoading, error, refetch };
}
```

## API Client
```typescript
// lib/api/transactions.ts
const API_URL = process.env.NEXT_PUBLIC_API_URL;

export async function getTransactions(filters?: TransactionFilters) {
  const params = new URLSearchParams(filters as Record<string, string>);
  const res = await fetch(`${API_URL}/api/transactions?${params}`, {
    headers: { Authorization: `Bearer ${getToken()}` },
  });
  
  if (!res.ok) {
    throw new Error('Failed to fetch transactions');
  }
  
  return res.json() as Promise<Transaction[]>;
}
```

## Error Handling
```typescript
// Error boundary for pages
'use client';

export default function Error({
  error,
  reset,
}: {
  error: Error;
  reset: () => void;
}) {
  return (
    <div>
      <h2>Something went wrong!</h2>
      <button onClick={reset}>Try again</button>
    </div>
  );
}
```

## Tailwind CSS
- Use shadcn/ui components as base
- Extend with Tailwind utilities
- Avoid inline styles
- Use CSS variables for theming

```tsx
// Good
<div className="flex items-center gap-4 p-4 rounded-lg bg-card">
  <span className="text-muted-foreground">Label</span>
</div>

// Bad
<div style={{ display: 'flex', alignItems: 'center' }}>
```

## Form Handling
```typescript
// Use react-hook-form + zod
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { z } from 'zod';

const schema = z.object({
  amount: z.number().positive(),
  category: z.string().min(1),
});

type FormData = z.infer<typeof schema>;

export function TransactionForm() {
  const form = useForm<FormData>({
    resolver: zodResolver(schema),
  });
  
  const onSubmit = (data: FormData) => {
    // handle submit
  };
  
  return (
    <form onSubmit={form.handleSubmit(onSubmit)}>
      {/* ... */}
    </form>
  );
}
```

## Loading States
```typescript
// Use Suspense for server components
<Suspense fallback={<TransactionTableSkeleton />}>
  <TransactionTable />
</Suspense>

// Use loading state for client components
{isLoading ? <Spinner /> : <DataDisplay data={data} />}
```

## Feature Folder Structure
```
components/features/
└── transactions/
    ├── TransactionTable.tsx
    ├── TransactionFilters.tsx
    ├── TransactionForm.tsx
    ├── TransactionDetail.tsx
    └── index.ts  # Re-exports
```
