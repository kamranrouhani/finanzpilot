---
active: true
iteration: 1
max_iterations: 70
completion_promise: "PHASE_3_COMPLETE."
started_at: "2026-01-22T00:44:19Z"
---


## Recovery & Resume Protocol
Before ANY work:
1. cat docs/iterations/PHASE_3_PROGRESS.md 2>/dev/null
2. git log --oneline -10
3. git branch --show-current (must be feat/phase-3)
4. ls -la backend/app/features/ frontend/src/components/features/

If progress file exists, resume from last incomplete item.
Do NOT recreate existing files — read and extend them.

## Progress Tracking (MANDATORY)
Create/update docs/iterations/PHASE_3_PROGRESS.md after EVERY deliverable:

# Phase 3 Progress
Last updated: [timestamp]
Current task: [description]

## Deliverables
- [ ] D1: Budget model + migration + CRUD endpoints + tests
- [ ] D2: Budget vs actual calculation logic + tests
- [ ] D3: Budget UI (list, form, progress bars)
- [ ] D4: Receipt-Transaction matching logic + tests
- [ ] D5: Receipt linking UI
- [ ] D6: AI category suggestion endpoint + tests (mock Ollama in tests)
- [ ] D7: Bulk categorization endpoint
- [ ] D8: AI insights generation endpoint + tests
- [ ] D9: Insights dashboard widget
- [ ] D10: Natural language chat endpoint + tests
- [ ] D11: Chat UI component
- [ ] D12: Polish (loading states, error boundaries, toasts)
- [ ] D13: E2E tests for critical flows
- [ ] D14: Final documentation + README

## Completed Files
[list files as completed]

## Blockers
[any issues]

Commit after each deliverable:
git add -A && git commit -m 'feat: [deliverable description]'
git add docs/iterations/PHASE_3_PROGRESS.md && git commit -m 'chore: update phase 3 progress'

## Pre-flight Check
1. docker ps (all services running)
2. curl -s http://localhost:8000/docs | head -5
3. curl -s http://localhost:11434/api/tags | head -5 (Ollama responding)
4. Phase 1 & 2 tests pass: docker compose exec backend pytest

If any fail, fix before proceeding.

## Context
Building FinanzPilot Phase 3: Budgets, AI Features & Polish.
Read @CLAUDE.md for full context.
Read @docs/SPEC.md for specifications.
Read @docs/PHASE_3.md for detailed requirements and AI prompts.

Phases 1-2 complete: Auth, Receipts, Transactions, Categories, Import, Dashboard working.

## AI Integration (CRITICAL)
- Ollama host: Use OLLAMA_HOST env var (http://ollama:11434 in Docker)
- Vision model: qwen2.5-vl:7b (for receipts)
- Text model: qwen2.5:7b (for chat, insights, categorization)
- ALWAYS handle Ollama connection errors gracefully
- In tests: Mock Ollama responses, don't require real model
- See @docs/PHASE_3.md for exact prompt templates

## Tech Stack (STRICT)
- Backend: FastAPI, SQLAlchemy 2.0, httpx (for Ollama calls)
- Frontend: Next.js 15, TypeScript, Tailwind, shadcn/ui, Recharts
- Package manager: pnpm (NOT npm)
- Tests: pytest + pytest-mock (backend), vitest (frontend), Playwright (E2E)

## Folder Structure (STRICT)
Backend AI feature: backend/app/features/ai/{router,service,schemas,ollama_client,prompts}.py
Backend budgets: backend/app/features/budgets/{router,service,schemas,models}.py
Frontend components: frontend/src/components/features/{budgets,ai}/
Frontend pages: frontend/src/app/(dashboard)/{budgets,chat}/page.tsx

## Working Rules
1. Check existing files BEFORE creating new ones
2. Write tests FIRST (TDD) — mock Ollama in tests
3. Run tests: docker compose exec backend pytest
4. Run frontend tests: docker compose exec frontend pnpm test
5. Format: docker compose exec backend black . && isort .
6. Commit after each working deliverable
7. Update progress file after each deliverable

## Task Order (from PHASE_3.md)
1. Budget model + migration
2. Budget CRUD tests → implementation
3. Budget vs actual calculation tests → implementation
4. Budget UI (list, form, progress visualization)
5. Receipt-transaction matching tests → implementation
6. Linking UI in transaction detail
7. AI categorization tests (mock Ollama) → implementation
8. Bulk categorization endpoint
9. AI insights tests → implementation
10. Insights widget on dashboard
11. Chat endpoint tests → implementation
12. Chat UI component
13. Add loading states, error boundaries, toast notifications
14. E2E tests (login, import, budget, chat)
15. Update README with user guide
16. Write PHASE_3_COMPLETE.md

## Verification Before Completion
- [ ] Can create and track budgets
- [ ] Budget progress updates with new transactions
- [ ] Can link receipt to transaction
- [ ] AI suggests categories (or gracefully fails if Ollama down)
- [ ] Insights widget shows data
- [ ] Chat answers spending questions
- [ ] All backend tests pass
- [ ] All frontend tests pass
- [ ] E2E tests pass
- [ ] No console errors in browser
- [ ] Mobile viewport works
- [ ] README has user guide

## Error Handling
Ollama timeout: Use 30s timeout, return graceful error message
AI hallucination: Validate JSON response, use confidence threshold
Budget calculation: Aggregate by category + period, handle nulls

## Output
When ALL deliverables verified:
<promise>PHASE_3_COMPLETE</promise>

If blocked:
<promise>BLOCKED</promise>
 use teh file in docs/PHASE_3.md as the main reference please
