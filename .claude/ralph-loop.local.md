---
active: true
iteration: 1
max_iterations: 50
completion_promise: "PHASE_1_COMPLETE"
started_at: "2026-01-21T01:51:00Z"
---


## Recovery & Resume Protocol (READ FIRST)
Before starting ANY work:
1. Check for existing progress file: cat docs/iterations/PHASE_1_PROGRESS.md 2>/dev/null
2. Check git history: git log --oneline -10
3. Check current branch: git branch --show-current
4. List existing files: ls -la backend/ frontend/ 2>/dev/null

If progress file exists, resume from last incomplete item.
If files exist but no progress file, audit what's done and create progress file.
Do NOT recreate existing files — read and continue from them.

## Progress Tracking (MANDATORY)
After EVERY completed deliverable, update docs/iterations/PHASE_1_PROGRESS.md:

# Phase 1 Progress
Last updated: [timestamp]
Current task: [what you're working on]

## Deliverables
- [x] D1: Docker Infrastructure
- [x] D2: Backend Foundation  
- [ ] D3: Authentication ← IN PROGRESS
- [ ] D4: Frontend Foundation
- [ ] D5: Basic Receipt OCR
- [ ] D6: Testing Infrastructure
- [ ] D7: Documentation

## Completed Files
- docker-compose.yml ✓
- backend/app/main.py ✓

## Next Steps
1. [immediate next task]
2. [following task]

## Blockers/Issues
- [any problems encountered]

Commit the progress file after each deliverable:
git add docs/iterations/PHASE_1_PROGRESS.md && git commit -m 'chore: update phase 1 progress'

## Pre-flight Check
Before coding, verify:
1. Docker running: docker ps
2. Ollama responds: curl -s http://localhost:11434/api/tags | head -5
3. Can write: touch test-write && rm test-write

If checks fail, output <promise>BLOCKED</promise> and explain why.

## Context
Building FinanzPilot Phase 1: Foundation.
Read @CLAUDE.md for project context.
Read @docs/SPEC.md for specifications.
Read @docs/PHASE_1.md for deliverables list.

## Folder Structure (STRICT)
Backend: feature-based in backend/app/features/<feature>/
Frontend: Next.js App Router in frontend/src/app/
Components: frontend/src/components/features/<feature>/
Use pnpm, NOT npm.

## Working Rules
1. Check existing files BEFORE creating
2. Write tests FIRST, then implementation
3. Run tests after each implementation
4. Commit after each working feature
5. Update progress file after each deliverable
6. Use conventional commits (feat:, fix:, test:, chore:)

## Git Workflow
Branch: feat/phase-1
Commit frequently with descriptive messages.
Push only when deliverable complete.

## Task Order
1. Docker infrastructure (docker-compose.yml)
2. Backend foundation (FastAPI structure)
3. Database setup (SQLAlchemy + Alembic)
4. User model + migration
5. Auth tests → Auth implementation
6. Frontend foundation (Next.js + Tailwind + shadcn)
7. Frontend auth pages
8. Receipt model + migration
9. Ollama integration
10. Receipt upload endpoint + UI
11. GitHub Actions CI workflow
12. Final documentation

## Verification Before Completion
Before outputting PHASE_1_COMPLETE, verify ALL:
- [ ] docker compose up starts all services
- [ ] Can register user: POST /api/auth/register
- [ ] Can login: POST /api/auth/login returns JWT
- [ ] Protected routes reject without token
- [ ] Can upload image and get OCR result
- [ ] All backend tests pass: docker compose exec backend pytest
- [ ] All frontend tests pass: docker compose exec frontend pnpm test
- [ ] No TypeScript errors: docker compose exec frontend pnpm type-check
- [ ] No Python lint errors: docker compose exec backend ruff check .
- [ ] Progress file is complete and accurate

## Error Handling
If a test fails:
1. Read the error carefully
2. Fix the issue
3. Re-run the test
4. Do NOT move on until green

If Docker fails:
1. Check logs: docker compose logs <service>
2. Check if port is in use: lsof -i :<port>
3. Rebuild if needed: docker compose build --no-cache <service>

If Ollama fails:
1. Check it's running: curl http://localhost:11434/api/tags
2. Check model exists: ollama list (should show qwen2.5-vl:7b)
3. Restart if needed: ollama serve

## Output
When ALL deliverables verified:
<promise>PHASE_1_COMPLETE</promise>

If blocked and cannot proceed:
<promise>BLOCKED</promise>

