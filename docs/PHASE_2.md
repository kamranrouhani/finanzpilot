# Phase 2: Data Import & Transaction Management

## Objective
Import Finanzguru data, build transaction management, and create the dashboard.

## Prerequisites
- [ ] Phase 1 completed and verified
- [ ] All Phase 1 tests passing
- [ ] Sample Finanzguru XLSX export ready in `sample-data/`

## Duration Estimate
- Ralph loop: 40-60 iterations
- Time: 6-10 hours (overnight run)
- API cost estimate: $40-80

## Deliverables

### D1: Finanzguru Import
- [ ] XLSX parser with full column mapping
- [ ] Account auto-creation from import
- [ ] Duplicate detection (hash-based)
- [ ] Batch insert for performance
- [ ] Progress tracking (WebSocket or polling)
- [ ] Import history/logs
- [ ] Tests with sample data

### D2: Category System
- [ ] Seed default categories (German)
- [ ] Seed tax categories (Steuerkategorien)
- [ ] Category CRUD endpoints
- [ ] Hierarchical category display
- [ ] Category icons (Lucide)
- [ ] Tests for category operations

### D3: Transaction Management
- [ ] List endpoint with pagination
- [ ] Filtering (date, category, amount, account, search)
- [ ] Single transaction CRUD
- [ ] Bulk category update
- [ ] Add notes/tags
- [ ] Transaction detail view
- [ ] Tests for all operations

### D4: Dashboard
- [ ] Monthly summary cards
- [ ] Income vs Expenses chart (Recharts)
- [ ] Category breakdown (donut chart)
- [ ] Recent transactions list
- [ ] Account balance overview
- [ ] Date range selector

### D5: Transaction UI
- [ ] Transaction list page with table
- [ ] Filters sidebar
- [ ] Pagination controls
- [ ] Quick category edit (inline)
- [ ] Transaction detail modal
- [ ] Import wizard UI

### D6: Testing & Documentation
- [ ] Integration tests for import
- [ ] E2E test: import flow
- [ ] `docs/iterations/PHASE_2_COMPLETE.md`

## Ralph Loop Prompt

```
/ralph-loop:ralph-loop "
## Context
You are building FinanzPilot Phase 2: Data Import & Transaction Management.
Read @CLAUDE.md for project context.
Read @docs/SPEC.md for specifications.
Phase 1 is complete - auth and basic receipt OCR work.

## Current Phase Objective
Import Finanzguru XLSX, build transaction management, create dashboard.

## Finanzguru Column Mapping (CRITICAL - use exactly)
See CLAUDE.md section 'Finanzguru Import Mapping' for exact column names.
German columns like 'Buchungstag', 'Beguenstigter/Auftraggeber', etc.
Date format: DD.MM.YYYY

## Working Rules
1. ALWAYS check existing files before creating new ones
2. Build on Phase 1 code - don't recreate
3. Write tests FIRST, then implementation
4. Run tests after each implementation
5. Commit after each working feat
6. Use existing auth/user context

## Git Workflow
1. Create branch: feat/phase-2
2. Commit after each feat
3. Run: make test before committing
4. Push only when all Phase 2 deliverables complete

## Task Order (follow strictly)
1. Create Category and TaxCategory models + migrations
2. Create seed data for German categories
3. Write category endpoint tests
4. Implement category CRUD endpoints
5. Create Transaction model + migration
6. Write Finanzguru parser tests (use sample data)
7. Implement XLSX parser with pandas
8. Write import endpoint tests
9. Implement import endpoint with duplicate detection
10. Write transaction CRUD tests
11. Implement transaction endpoints (list, filter, update)
12. Create dashboard API endpoints (stats, charts)
13. Build category management UI
14. Build import wizard UI with progress
15. Build transaction list page with filters
16. Build dashboard page with charts
17. Write E2E test for import flow
18. Write PHASE_2_COMPLETE.md

## Sample Finanzguru Data Location
./sample-data/finanzguru_export.xlsx

## Verification Checklist
- [ ] Can import Finanzguru XLSX via API
- [ ] Duplicate transactions not re-imported
- [ ] Can list transactions with filters
- [ ] Can update transaction category
- [ ] Dashboard shows correct totals
- [ ] Charts render correctly
- [ ] All tests pass
- [ ] No TypeScript/Python errors

## If Stuck
- For XLSX parsing: use pandas with openpyxl engine
- For charts: use Recharts library
- For date parsing: German format is DD.MM.YYYY
- For amount: German uses comma as decimal (1.234,56)

## Output
When ALL deliverables complete and verified:
<promise>PHASE_2_COMPLETE</promise>
" --max-iterations 60 --completion-promise "PHASE_2_COMPLETE"
```

## Manual Verification After Ralph

### 1. Test Import
```bash
# Import Finanzguru data
curl -X POST http://localhost:8000/api/transactions/import \
  -H "Authorization: Bearer <token>" \
  -F "file=@sample-data/finanzguru_export.xlsx"

# Check import results
curl http://localhost:8000/api/transactions?limit=10 \
  -H "Authorization: Bearer <token>"
```

### 2. Test Duplicate Detection
```bash
# Import same file again
curl -X POST http://localhost:8000/api/transactions/import \
  -H "Authorization: Bearer <token>" \
  -F "file=@sample-data/finanzguru_export.xlsx"
# Should report 0 new transactions
```

### 3. Test Filtering
```bash
# Filter by date range
curl "http://localhost:8000/api/transactions?start_date=2023-01-01&end_date=2023-12-31" \
  -H "Authorization: Bearer <token>"

# Filter by category
curl "http://localhost:8000/api/transactions?category=Lebensmittel" \
  -H "Authorization: Bearer <token>"

# Search
curl "http://localhost:8000/api/transactions?search=REWE" \
  -H "Authorization: Bearer <token>"
```

### 4. Test Dashboard
1. Open http://localhost:3000
2. Login
3. Dashboard should show:
   - Monthly income/expense totals
   - Category breakdown chart
   - Recent transactions

### 5. Test Transaction UI
1. Navigate to /transactions
2. Should see imported transactions
3. Try filtering by date, category
4. Click transaction to see details
5. Try changing category

## Potential Issues & Solutions

| Issue | Solution |
|-------|----------|
| XLSX parse error | Check pandas + openpyxl installed |
| German date format | Use dateutil.parser or strptime with %d.%m.%Y |
| Amount parsing | Replace comma with dot, handle thousands separator |
| Large import slow | Use bulk insert, batch commits |
| Chart not rendering | Check Recharts data format |

## Database Seed Data

### Default Categories (created in migration)
```python
SEED_CATEGORIES = [
    {"name": "Income", "name_de": "Einnahmen", "is_income": True, "children": [
        {"name": "Salary", "name_de": "Gehalt"},
        {"name": "Freelance", "name_de": "Freiberuflich"},
        {"name": "Other Income", "name_de": "Sonstige Einnahmen"},
    ]},
    {"name": "Food & Groceries", "name_de": "Lebensmittel", "children": [
        {"name": "Supermarket", "name_de": "Supermarkt"},
        {"name": "Restaurant", "name_de": "Restaurant"},
        {"name": "Delivery", "name_de": "Lieferservice"},
    ]},
    {"name": "Housing", "name_de": "Wohnen", "children": [
        {"name": "Rent", "name_de": "Miete"},
        {"name": "Utilities", "name_de": "Nebenkosten"},
        {"name": "Internet", "name_de": "Internet"},
    ]},
    {"name": "Transportation", "name_de": "Mobilität", "children": [
        {"name": "Public Transit", "name_de": "ÖPNV"},
        {"name": "Fuel", "name_de": "Tanken"},
        {"name": "Car", "name_de": "Auto"},
    ]},
    {"name": "Shopping", "name_de": "Einkaufen", "children": [
        {"name": "Clothing", "name_de": "Kleidung"},
        {"name": "Electronics", "name_de": "Elektronik"},
        {"name": "Household", "name_de": "Haushalt"},
    ]},
    {"name": "Health", "name_de": "Gesundheit", "children": [
        {"name": "Pharmacy", "name_de": "Apotheke"},
        {"name": "Doctor", "name_de": "Arzt"},
        {"name": "Insurance", "name_de": "Versicherung"},
    ]},
    {"name": "Entertainment", "name_de": "Freizeit", "children": [
        {"name": "Subscriptions", "name_de": "Abonnements"},
        {"name": "Sports", "name_de": "Sport"},
        {"name": "Culture", "name_de": "Kultur"},
    ]},
    {"name": "Transfers", "name_de": "Umbuchungen"},
    {"name": "Other", "name_de": "Sonstiges"},
]
```

### Tax Categories (Steuerkategorien)
```python
SEED_TAX_CATEGORIES = [
    {"name": "work_equipment", "name_de": "Arbeitsmittel", "anlage": "N"},
    {"name": "commuting", "name_de": "Fahrtkosten", "anlage": "N"},
    {"name": "professional_development", "name_de": "Fortbildung", "anlage": "N"},
    {"name": "home_office", "name_de": "Homeoffice-Pauschale", "anlage": "N"},
    {"name": "insurance", "name_de": "Versicherungen", "anlage": "Vorsorgeaufwand"},
    {"name": "donations", "name_de": "Spenden", "anlage": "Sonderausgaben"},
    {"name": "craftsman_services", "name_de": "Handwerkerleistungen", "anlage": "Haushaltsnahe"},
    {"name": "household_services", "name_de": "Haushaltsnahe Dienstleistungen", "anlage": "Haushaltsnahe"},
    {"name": "medical_expenses", "name_de": "Krankheitskosten", "anlage": "Außergewöhnliche Belastungen"},
    {"name": "childcare", "name_de": "Kinderbetreuung", "anlage": "Kind"},
]
```

## Files Created This Phase

```
finanzpilot/
├── backend/
│   ├── alembic/versions/
│   │   ├── 002_categories.py
│   │   └── 003_transactions.py
│   ├── app/
│   │   ├── features/
│   │   │   ├── categories/
│   │   │   │   ├── router.py
│   │   │   │   ├── service.py
│   │   │   │   ├── schemas.py
│   │   │   │   └── models.py
│   │   │   └── transactions/
│   │   │       ├── router.py
│   │   │       ├── service.py
│   │   │       ├── schemas.py
│   │   │       ├── models.py
│   │   │       └── import_service.py
│   │   └── shared/
│   │       └── seed_data.py
│   └── tests/
│       ├── test_categories.py
│       ├── test_transactions.py
│       └── test_import.py
├── frontend/
│   ├── src/
│   │   ├── app/(dashboard)/
│   │   │   ├── page.tsx (dashboard)
│   │   │   └── transactions/
│   │   │       ├── page.tsx
│   │   │       └── [id]/page.tsx
│   │   ├── components/features/
│   │   │   ├── dashboard/
│   │   │   │   ├── SummaryCards.tsx
│   │   │   │   ├── CategoryChart.tsx
│   │   │   │   └── RecentTransactions.tsx
│   │   │   └── transactions/
│   │   │       ├── TransactionTable.tsx
│   │   │       ├── TransactionFilters.tsx
│   │   │       ├── TransactionDetail.tsx
│   │   │       └── ImportWizard.tsx
│   │   └── lib/api/
│   │       ├── transactions.ts
│   │       └── categories.ts
│   └── tests/
│       ├── components/
│       │   └── transactions.test.tsx
│       └── e2e/
│           └── import.spec.ts
└── docs/iterations/
    └── PHASE_2_COMPLETE.md
```

## Next Phase Preview
Phase 3 will add:
- Budget management
- AI-powered insights
- Receipt-transaction linking
- Natural language queries

---

**Start command:**
```bash
cd ~/projects/finanzpilot
git checkout -b feat/phase-2
claude
# Then paste the Ralph loop prompt
```
