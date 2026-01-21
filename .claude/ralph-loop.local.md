---
active: true
iteration: 1
max_iterations: 60
completion_promise: "PHASE_2_COMPLETE"
started_at: "2026-01-21T09:50:03Z"
---


## Recovery & Resume Protocol
Before ANY work:
1. cat docs/iterations/PHASE_2_PROGRESS.md 2>/dev/null
2. git log --oneline -10
3. git branch --show-current (must be feat/phase-2)
4. ls -la backend/app/features/ frontend/src/app/

If progress file exists, resume from last incomplete item.
Do NOT recreate existing files — read and extend them.

## Progress Tracking (MANDATORY)
Create/update docs/iterations/PHASE_2_PROGRESS.md after EVERY deliverable:

# Phase 2 Progress
Last updated: [timestamp]
Current task: [description]

## Deliverables
- [ ] D1: Category & TaxCategory models + seed data
- [ ] D2: Category CRUD endpoints + tests
- [ ] D3: Transaction model + migration
- [ ] D4: Finanzguru XLSX parser + tests
- [ ] D5: Transaction import endpoint (with duplicate detection)
- [ ] D6: Transaction CRUD + filtering endpoints + tests
- [ ] D7: Dashboard stats endpoints
- [ ] D8: Frontend: Category management UI
- [ ] D9: Frontend: Import wizard with progress
- [ ] D10: Frontend: Transaction list with filters
- [ ] D11: Frontend: Dashboard with charts (Recharts)
- [ ] D12: E2E test: import flow
- [ ] D13: Documentation

## Completed Files
[list files as completed]

## Blockers
[any issues]

Commit after each deliverable:
git add -A && git commit -m 'feat: [deliverable description]'
git add docs/iterations/PHASE_2_PROGRESS.md && git commit -m 'chore: update phase 2 progress'

## Pre-flight Check
1. docker ps (postgres, backend, frontend running)
2. curl -s http://localhost:8000/docs | head -5 (API responding)
3. All Phase 1 tests still pass: docker compose exec backend pytest

If any fail, fix before proceeding.

## Context
Building FinanzPilot Phase 2: Data Import & Transaction Management.
Read @CLAUDE.md for full context (especially Finanzguru column mapping and German tax categories).
Read @docs/SPEC.md for database schema.
Read @docs/PHASE_2.md for detailed requirements.

Phase 1 complete: Auth, Receipt OCR, Docker infrastructure working.

## Finanzguru Import (CRITICAL)
Column mapping from CLAUDE.md - use EXACTLY:
- Buchungstag → date (format: DD.MM.YYYY)
- Betrag → amount (German decimal: comma, e.g., -45,67)
- Beguenstigter/Auftraggeber → counterparty
- Verwendungszweck → description
- Analyse-Hauptkategorie → category
- Analyse-Unterkategorie → subcategory
... (see full mapping in CLAUDE.md)

Duplicate detection: hash(date + amount + counterparty + description)

## Tech Stack (STRICT)
- Backend: FastAPI, SQLAlchemy 2.0, Alembic, pandas (for XLSX)
- Frontend: Next.js 15 App Router, TypeScript, Tailwind, shadcn/ui, Recharts
- Package manager: pnpm (NOT npm)
- Tests: pytest (backend), vitest (frontend)

## Folder Structure (STRICT)
Backend features: backend/app/features/<feature>/{router,service,schemas,models}.py
Frontend pages: frontend/src/app/(dashboard)/<page>/page.tsx
Frontend components: frontend/src/components/features/<feature>/
API client: frontend/src/lib/api/<feature>.ts

## Working Rules
1. Check existing files BEFORE creating new ones
2. Write tests FIRST (TDD)
3. Run tests after implementation: docker compose exec backend pytest
4. Run frontend tests: docker compose exec frontend pnpm test
5. Format backend: docker compose exec backend black . && isort .
6. Commit after each working deliverable
7. Update progress file after each deliverable

## Task Order
1. Create Category model with parent_id for hierarchy
2. Create TaxCategory model (German: Werbungskosten, Sonderausgaben, etc.)
3. Create seed data migration for default categories
4. Write category endpoint tests
5. Implement category CRUD endpoints
6. Create Transaction model (see SPEC.md for full schema)
7. Write Finanzguru parser tests with sample data
8. Implement XLSX parser (pandas + openpyxl)
9. Write import endpoint tests
10. Implement import endpoint with duplicate detection + progress
11. Write transaction CRUD tests
12. Implement transaction list with pagination + filters
13. Implement dashboard stats endpoint (monthly totals, category breakdown)
14. Build category management UI (list, create, edit)
15. Build import wizard UI (upload, preview, confirm, progress bar)
16. Build transaction list page (table, filters, pagination, inline category edit)
17. Build dashboard (summary cards, Recharts charts)
18. Write E2E test for import flow
19. Update documentation

## Verification Before Completion
- [ ] Can import Finanzguru XLSX via API
- [ ] Re-importing same file creates 0 duplicates
- [ ] Transaction list shows data with working filters
- [ ] Can change transaction category
- [ ] Dashboard shows correct monthly totals
- [ ] Charts render with real data
- [ ] All backend tests pass
- [ ] All frontend tests pass
- [ ] No lint errors
- [ ] Progress file complete

## Error Handling
XLSX parse errors: Check pandas + openpyxl installed, check date format (DD.MM.YYYY)
Amount parsing: German format uses comma (replace , with . for float)
Large import slow: Use bulk_insert_mappings, commit in batches of 1000

## Output
When ALL deliverables verified:
<promise>PHASE_2_COMPLETE</promise>

If blocked:
<promise>BLOCKED</promise>

