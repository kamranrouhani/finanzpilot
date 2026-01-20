# Phase 1: Foundation

## Objective
Set up project infrastructure, authentication, and basic receipt OCR functionality.

## Duration Estimate
- Ralph loop: 30-50 iterations
- Time: 4-8 hours (overnight run)
- API cost estimate: $30-60

## Prerequisites Checklist
Before starting Ralph, verify:
- [ ] All items in `docs/PREREQUISITES.md` completed
- [ ] Docker with GPU support working
- [ ] Ollama models pre-pulled
- [ ] Git repo initialized
- [ ] `.env` file created

## Deliverables

### D1: Docker Infrastructure
- [ ] `docker-compose.yml` with all services
- [ ] `docker-compose.dev.yml` for development (hot reload)
- [ ] PostgreSQL with named volume
- [ ] Ollama with GPU passthrough
- [ ] FastAPI backend container
- [ ] Next.js frontend container
- [ ] Health checks for all services

### D2: Backend Foundation
- [ ] FastAPI project structure (feature-based)
- [ ] SQLAlchemy 2.0 setup with async
- [ ] Alembic migrations configured
- [ ] Database models: User, Account, Category, TaxCategory
- [ ] Pydantic schemas for all models
- [ ] CORS configuration
- [ ] Error handling middleware
- [ ] Logging setup

### D3: Authentication System
- [ ] User registration endpoint
- [ ] Login endpoint (returns JWT)
- [ ] Password hashing with bcrypt
- [ ] JWT token generation/validation
- [ ] Protected route decorator
- [ ] Current user endpoint

### D4: Frontend Foundation
- [ ] Next.js 15 with App Router
- [ ] TypeScript configuration
- [ ] Tailwind CSS setup
- [ ] shadcn/ui initialization
- [ ] Basic layout component
- [ ] Auth context/provider
- [ ] Login page
- [ ] Register page
- [ ] Protected route wrapper

### D5: Basic Receipt OCR
- [ ] Receipt upload endpoint
- [ ] File validation (type, size)
- [ ] Ollama integration service
- [ ] German receipt extraction prompt
- [ ] Receipt model and migration
- [ ] Simple upload UI component
- [ ] Display extracted data

### D6: Testing Infrastructure
- [ ] pytest configuration
- [ ] Test database fixture
- [ ] Vitest configuration
- [ ] Sample test for each feature
- [ ] GitHub Actions CI workflow

### D7: Documentation
- [ ] API documentation (auto-generated)
- [ ] `docs/iterations/PHASE_1_COMPLETE.md`

## Ralph Loop Prompt

```
/ralph-loop:ralph-loop "
## Context
You are building FinanzPilot Phase 1: Foundation.
Read @CLAUDE.md for full project context.
Read @docs/SPEC.md for detailed specifications.

## Current Phase Objective
Set up Docker infrastructure, authentication, and basic receipt OCR.

## Working Rules
1. ALWAYS check existing files before creating new ones
2. Use feature-based folder structure as defined in CLAUDE.md
3. Write tests FIRST, then implementation (TDD)
4. Run tests after each implementation
5. Commit after each working feature with conventional commit message
6. If tests fail, fix before moving on

## Git Workflow
1. You are on branch: feature/phase-1
2. After each feature: git add . && git commit -m 'feat: description'
3. Run: make test (or equivalent) before committing
4. Do NOT push until all Phase 1 deliverables complete

## Task Order (follow strictly)
1. Create docker-compose.yml with postgres, ollama services
2. Create backend Dockerfile and project structure
3. Set up SQLAlchemy + Alembic
4. Create User model and migration
5. Write auth tests (test_auth.py)
6. Implement auth endpoints to pass tests
7. Create frontend Dockerfile and Next.js project
8. Set up Tailwind + shadcn
9. Write frontend auth component tests
10. Implement login/register pages
11. Create Receipt model and migration
12. Write receipt upload tests
13. Implement Ollama integration
14. Implement receipt upload endpoint
15. Create receipt upload UI
16. Set up GitHub Actions CI
17. Write PHASE_1_COMPLETE.md documentation

## Verification Checklist (check before outputting COMPLETE)
- [ ] docker compose up starts all services without errors
- [ ] Can register new user via API
- [ ] Can login and receive JWT
- [ ] Protected endpoints reject without token
- [ ] Can upload image and get OCR result
- [ ] All backend tests pass (pytest)
- [ ] All frontend tests pass (vitest)
- [ ] No TypeScript errors
- [ ] No Python linting errors

## If Stuck
- Check Docker logs: docker compose logs <service>
- Check Ollama is responding: curl http://localhost:11434/api/tags
- Verify GPU access: docker exec ollama nvidia-smi
- If model not found: docker exec ollama ollama pull qwen2.5-vl:7b

## Output
When ALL deliverables are complete and verified:
<promise>PHASE_1_COMPLETE</promise>
" --max-iterations 50 --completion-promise "PHASE_1_COMPLETE"
```

## Manual Verification After Ralph

Once Ralph outputs `PHASE_1_COMPLETE`, manually verify:

### 1. Start Services
```bash
cd ~/projects/finanzpilot
docker compose up -d
docker compose logs -f  # Watch for errors
```

### 2. Test Authentication
```bash
# Register
curl -X POST http://localhost:8000/api/auth/register \
  -H "Content-Type: application/json" \
  -d '{"username": "testuser", "password": "testpass123"}'

# Login
curl -X POST http://localhost:8000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username": "testuser", "password": "testpass123"}'
# Save the token from response

# Test protected endpoint
curl http://localhost:8000/api/auth/me \
  -H "Authorization: Bearer <token>"
```

### 3. Test Receipt OCR
```bash
# Upload a receipt image
curl -X POST http://localhost:8000/api/receipts \
  -H "Authorization: Bearer <token>" \
  -F "file=@sample-data/receipts/test_receipt.jpg"
```

### 4. Test Frontend
1. Open http://localhost:3000
2. Register a new account
3. Login
4. Should see dashboard (empty for now)

### 5. Run Full Test Suite
```bash
make test
# or
docker compose exec backend pytest
docker compose exec frontend pnpm test
```

## Potential Issues & Solutions

| Issue | Solution |
|-------|----------|
| Ollama OOM | Reduce to qwen2.5-vl:2b or close other GPU apps |
| Database connection refused | Wait 30s for postgres to initialize |
| CORS errors | Check CORS config includes localhost:3000 |
| JWT decode error | Verify JWT_SECRET matches in .env |
| File upload 413 | Increase nginx/FastAPI body size limit |

## Files Created This Phase

```
finanzpilot/
├── docker-compose.yml
├── docker-compose.dev.yml
├── Makefile
├── .env.example
├── .gitignore
├── backend/
│   ├── Dockerfile
│   ├── requirements.txt
│   ├── alembic.ini
│   ├── alembic/
│   │   └── versions/
│   │       └── 001_initial.py
│   ├── app/
│   │   ├── main.py
│   │   ├── config.py
│   │   ├── database.py
│   │   ├── features/
│   │   │   ├── auth/
│   │   │   │   ├── router.py
│   │   │   │   ├── service.py
│   │   │   │   ├── schemas.py
│   │   │   │   └── models.py
│   │   │   └── receipts/
│   │   │       ├── router.py
│   │   │       ├── service.py
│   │   │       ├── schemas.py
│   │   │       └── models.py
│   │   └── shared/
│   │       ├── models.py
│   │       └── dependencies.py
│   └── tests/
│       ├── conftest.py
│       ├── test_auth.py
│       └── test_receipts.py
├── frontend/
│   ├── Dockerfile
│   ├── package.json
│   ├── next.config.js
│   ├── tailwind.config.js
│   ├── tsconfig.json
│   ├── src/
│   │   ├── app/
│   │   │   ├── layout.tsx
│   │   │   ├── page.tsx
│   │   │   ├── (auth)/
│   │   │   │   ├── login/page.tsx
│   │   │   │   └── register/page.tsx
│   │   │   └── (dashboard)/
│   │   │       ├── layout.tsx
│   │   │       └── page.tsx
│   │   ├── components/
│   │   │   ├── ui/  (shadcn)
│   │   │   └── features/
│   │   │       └── auth/
│   │   │           ├── LoginForm.tsx
│   │   │           └── RegisterForm.tsx
│   │   └── lib/
│   │       ├── api/
│   │       │   └── auth.ts
│   │       └── auth-context.tsx
│   └── tests/
│       └── components/
│           └── auth.test.tsx
├── .github/
│   └── workflows/
│       └── ci.yml
└── docs/
    └── iterations/
        └── PHASE_1_COMPLETE.md
```

## Next Phase Preview
Phase 2 will add:
- Finanzguru XLSX import
- Transaction management
- Category system
- Basic dashboard

---

**Start command:**
```bash
cd ~/projects/finanzpilot
git checkout -b feature/phase-1
claude
# Then paste the Ralph loop prompt
```
