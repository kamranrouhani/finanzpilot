# FinanzPilot - Local AI Financial Advisor

## Project Overview
A fully local, privacy-first personal finance application for German users. Uses local LLMs (Ollama + Qwen2.5-VL) for receipt OCR and financial analysis. All data stays on the user's machine.

## Tech Stack
- **Frontend**: Next.js 15 (App Router), TypeScript, Tailwind CSS, shadcn/ui
- **Backend**: FastAPI (Python 3.12), SQLAlchemy 2.0, Alembic
- **Database**: PostgreSQL 16 (Docker)
- **AI/ML**: Ollama + Qwen2.5-VL-7B (vision), Qwen2.5:7b (text)
- **Auth**: Local username/password (bcrypt + JWT)
- **Testing**: pytest + pytest-cov (backend), Vitest + RTL (frontend), Playwright (E2E)
- **CI**: GitHub Actions

## Architecture
```
┌─────────────────────────────────────────────────────────────────┐
│                        Docker Compose                           │
├─────────────────────────────────────────────────────────────────┤
│  ┌──────────────┐    ┌──────────────┐    ┌──────────────────┐  │
│  │   Next.js    │◄──►│   FastAPI    │◄──►│     Ollama       │  │
│  │   :3000      │    │   :8000      │    │  :11434 (GPU)    │  │
│  └──────────────┘    └──────────────┘    └──────────────────┘  │
│         │                   │                                   │
│         └───────────────────┼───────────────────────────────┐   │
│                             ▼                               │   │
│                      ┌──────────────┐                       │   │
│                      │  PostgreSQL  │◄──────────────────────┘   │
│                      │   :5432      │   (Named Volume)          │
│                      └──────────────┘                           │
└─────────────────────────────────────────────────────────────────┘
```

## Folder Structure (Feature-Based)
```
finanzpilot/
├── frontend/
│   ├── src/
│   │   ├── app/                    # Next.js App Router
│   │   │   ├── (auth)/             # Auth routes group
│   │   │   │   ├── login/
│   │   │   │   └── register/
│   │   │   ├── (dashboard)/        # Protected routes
│   │   │   │   ├── layout.tsx
│   │   │   │   ├── page.tsx        # Dashboard home
│   │   │   │   ├── transactions/
│   │   │   │   ├── receipts/
│   │   │   │   ├── budgets/
│   │   │   │   └── settings/
│   │   │   ├── layout.tsx
│   │   │   └── page.tsx            # Landing/redirect
│   │   ├── components/
│   │   │   ├── ui/                 # shadcn components
│   │   │   └── features/           # Feature-specific components
│   │   │       ├── auth/
│   │   │       ├── transactions/
│   │   │       ├── receipts/
│   │   │       └── budgets/
│   │   ├── lib/
│   │   │   ├── api/                # API client functions
│   │   │   ├── hooks/              # Custom React hooks
│   │   │   └── utils/              # Utility functions
│   │   └── types/                  # TypeScript types
│   ├── tests/
│   │   ├── unit/
│   │   └── e2e/
│   └── package.json
├── backend/
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
│   │   │   ├── transactions/
│   │   │   ├── receipts/
│   │   │   ├── budgets/
│   │   │   └── ai/
│   │   └── shared/
│   │       ├── models.py           # Base models
│   │       └── dependencies.py
│   ├── alembic/
│   ├── tests/
│   │   ├── conftest.py
│   │   ├── unit/
│   │   └── integration/
│   └── requirements.txt
├── docs/
│   ├── SPEC.md
│   ├── PREREQUISITES.md
│   ├── PHASE_1.md
│   ├── PHASE_2.md
│   ├── PHASE_3.md
│   └── iterations/                 # Post-iteration docs
├── docker-compose.yml
├── .github/
│   └── workflows/
│       └── ci.yml
└── CLAUDE.md
```

## Git Workflow
1. All work happens on `feature/<name>` branches
2. Write tests FIRST (TDD approach)
3. Implement feature to pass tests
4. Run tests locally: `make test`
5. Run linting: `make lint`
6. If local CI passes, push and create PR
7. GitHub Actions runs on PR
8. Merge to `main` only when CI green
9. After each phase, create iteration doc in `docs/iterations/`

## Commands
```bash
# Development
make dev              # Start all services
make test             # Run all tests
make test-backend     # Backend tests only
make test-frontend    # Frontend tests only
make lint             # Run all linters
make db-migrate       # Run Alembic migrations

# Docker
make up               # docker-compose up -d
make down             # docker-compose down
make logs             # docker-compose logs -f
make rebuild          # Rebuild containers

# CI simulation
make ci-local         # Run full CI pipeline locally
```

## Database Schema (Core Tables)
```sql
-- Users (single user for now, but ready for multi)
users: id, username, password_hash, created_at

-- Accounts (bank accounts from Finanzguru)
accounts: id, user_id, name, iban_last4, type, currency, created_at

-- Transactions (main financial data)
transactions: id, user_id, account_id, date, amount, currency, 
              counterparty, iban_counterparty, description, 
              category_id, subcategory_id, tax_category_id,
              is_recurring, contract_name, source, created_at

-- Categories
categories: id, name, name_de, parent_id, is_income, icon

-- Tax Categories (German specific)
tax_categories: id, name, name_de, anlage, description

-- Receipts
receipts: id, user_id, transaction_id, image_path, 
          ocr_result, extracted_data, processed_at

-- Budgets
budgets: id, user_id, category_id, amount, period, start_date
```

## German Tax Categories (Steuerkategorien)
```python
TAX_CATEGORIES = {
    "werbungskosten": {
        "name_de": "Werbungskosten",
        "anlage": "N",
        "subcategories": [
            "arbeitsmittel",           # Work equipment
            "fahrtkosten",             # Commuting costs
            "fortbildung",             # Professional development
            "home_office",             # Home office deduction
            "doppelte_haushaltsfuehrung",  # Double household
        ]
    },
    "sonderausgaben": {
        "name_de": "Sonderausgaben",
        "anlage": "Sonderausgaben",
        "subcategories": [
            "versicherungen",          # Insurance
            "spenden",                 # Donations
            "altersvorsorge",          # Retirement savings
            "kirchensteuer",           # Church tax
        ]
    },
    "haushaltsnahe_dienstleistungen": {
        "name_de": "Haushaltsnahe Dienstleistungen",
        "anlage": "Haushaltsnahe",
        "subcategories": [
            "handwerkerleistungen",    # Craftsman services
            "haushaltshilfe",          # Household help
            "gartenpflege",            # Garden maintenance
        ]
    },
    "aussergewoehnliche_belastungen": {
        "name_de": "Außergewöhnliche Belastungen",
        "anlage": "Außergewöhnliche Belastungen",
        "subcategories": [
            "krankheitskosten",        # Medical expenses
            "pflegekosten",            # Care costs
            "behinderung",             # Disability-related
        ]
    },
}
```

## Finanzguru Import Mapping
```python
FINANZGURU_COLUMNS = {
    "Buchungstag": "date",
    "Referenzkonto": "account_iban",
    "Name Referenzkonto": "account_name", 
    "Betrag": "amount",
    "Kontostand": "balance",
    "Waehrung": "currency",
    "Beguenstigter/Auftraggeber": "counterparty",
    "IBAN Beguenstigter/Auftraggeber": "counterparty_iban",
    "Verwendungszweck": "description",
    "E-Ref": "e_ref",
    "Mandatsreferenz": "mandate_ref",
    "Glaeubiger-ID": "creditor_id",
    "Analyse-Hauptkategorie": "category",
    "Analyse-Unterkategorie": "subcategory",
    "Analyse-Vertrag": "contract",
    "Analyse-Vertragsturnus": "contract_frequency",
    "Analyse-Vertrags-ID": "contract_id",
    "Analyse-Umbuchung": "is_transfer",
    "Analyse-Vom frei verfuegbaren Einkommen ausgeschlossen": "excluded_from_budget",
    "Analyse-Umsatzart": "transaction_type",
    "Analyse-Betrag": "analysis_amount",
    "Analyse-Woche": "week",
    "Analyse-Monat": "month",
    "Analyse-Quartal": "quarter",
    "Analyse-Jahr": "year",
    "Tags": "tags",
    "Notiz": "notes",
}
```

## AI Prompts

### Receipt Extraction (German)
```
Analysiere diesen deutschen Kassenbon/Rechnung und extrahiere als JSON:
{
  "haendler": "Name des Geschäfts",
  "datum": "YYYY-MM-DD",
  "gesamt_brutto": 0.00,
  "mwst_7": 0.00,
  "mwst_19": 0.00,
  "positionen": [{"artikel": "", "menge": 1, "einzelpreis": 0.00, "gesamtpreis": 0.00}],
  "zahlungsart": "Bar|EC|Kreditkarte",
  "kategorie_vorschlag": "Lebensmittel|Haushalt|Drogerie|Restaurant|..."
}
Gib NUR valides JSON zurück, keine Erklärungen.
```

### Category Suggestion
```
Based on this transaction, suggest the most appropriate category:
- Counterparty: {counterparty}
- Description: {description}
- Amount: {amount} EUR

Respond with JSON: {"category": "...", "subcategory": "...", "confidence": 0.0-1.0}
```

## Environment Variables
```bash
# Backend
DATABASE_URL=postgresql://finanzpilot:secret@postgres:5432/finanzpilot
OLLAMA_HOST=http://ollama:11434
JWT_SECRET=<generate-secure-secret>
JWT_ALGORITHM=HS256
JWT_EXPIRE_MINUTES=1440

# Frontend
NEXT_PUBLIC_API_URL=http://localhost:8000
```

## Testing Requirements
- Backend: >80% coverage on business logic
- Frontend: All components have unit tests
- E2E: Critical user flows (login, import, receipt upload)
- All tests must pass before merge

## Code Style
- Python: Black, isort, ruff
- TypeScript: ESLint, Prettier
- Commits: Conventional commits (feat:, fix:, docs:, test:, chore:)

## Critical Rules
1. NEVER store sensitive data unencrypted
2. ALL database operations use transactions
3. ALL API endpoints require authentication (except /auth/*)
4. ALL file uploads validated (type, size)
5. ALL user input sanitized
6. PostgreSQL data persisted via Docker named volume
7. Graceful shutdown handling for data integrity

## Current Phase
Phase 1: Foundation (Auth + Infrastructure + Basic Receipt OCR)

## References
- @docs/SPEC.md - Full specification
- @docs/PREREQUISITES.md - Setup checklist
- @docs/PHASE_1.md - Current phase details
