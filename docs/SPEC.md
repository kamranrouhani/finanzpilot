# FinanzPilot - Full Specification

## Vision
A fully local, privacy-first personal finance application designed for German users. Leverages local LLMs for receipt OCR and intelligent financial analysis. All data remains on the user's machine—no cloud dependencies.

## Core Requirements

### Functional Requirements

#### FR1: Authentication
- FR1.1: User registration with username/password
- FR1.2: Secure login with JWT tokens
- FR1.3: Session persistence (7-day expiry)
- FR1.4: Logout functionality
- FR1.5: Password hashing with bcrypt

#### FR2: Data Import
- FR2.1: Import Finanzguru XLSX exports (full column mapping)
- FR2.2: Handle 3-4 years of transaction history (50,000+ rows)
- FR2.3: Duplicate detection on re-import
- FR2.4: Progress indicator for large imports
- FR2.5: Preserve original Finanzguru categories

#### FR3: Receipt Processing
- FR3.1: Upload receipt images (JPG, PNG, PDF)
- FR3.2: Local OCR via Qwen2.5-VL-7B
- FR3.3: Extract: merchant, date, total, line items, VAT
- FR3.4: Link receipts to existing transactions
- FR3.5: Store original images locally

#### FR4: Transaction Management
- FR4.1: View all transactions with pagination
- FR4.2: Filter by date, category, amount, account
- FR4.3: Search by counterparty or description
- FR4.4: Edit transaction categories
- FR4.5: Add notes and tags
- FR4.6: Bulk categorization

#### FR5: Categorization
- FR5.1: Hierarchical categories (main + sub)
- FR5.2: German tax categories (Steuerkategorien)
- FR5.3: AI-suggested categories for uncategorized transactions
- FR5.4: Custom category creation
- FR5.5: Category rules (auto-categorize by counterparty)

#### FR6: Budgets
- FR6.1: Set monthly budgets per category
- FR6.2: Track spending vs budget
- FR6.3: Visual progress indicators
- FR6.4: AI recommendations based on spending patterns
- FR6.5: Recurring expense detection

#### FR7: Analytics & Dashboard
- FR7.1: Monthly spending overview
- FR7.2: Category breakdown charts
- FR7.3: Income vs expenses trend
- FR7.4: Year-over-year comparison
- FR7.5: Tax-relevant expense summary

#### FR8: AI Assistant
- FR8.1: Natural language queries ("How much did I spend on groceries in March?")
- FR8.2: Spending insights and anomaly detection
- FR8.3: Savings recommendations
- FR8.4: German language support

### Non-Functional Requirements

#### NFR1: Privacy & Security
- NFR1.1: All data stored locally (PostgreSQL in Docker)
- NFR1.2: All AI processing local (Ollama)
- NFR1.3: No external API calls for user data
- NFR1.4: Encrypted passwords (bcrypt, cost factor 12)
- NFR1.5: JWT tokens with short expiry

#### NFR2: Reliability
- NFR2.1: PostgreSQL data persisted via Docker named volumes
- NFR2.2: Graceful shutdown handling
- NFR2.3: Transaction rollback on errors
- NFR2.4: No data loss on unexpected restarts
- NFR2.5: Database backups via pg_dump

#### NFR3: Performance
- NFR3.1: Dashboard loads in <2 seconds
- NFR3.2: Transaction list pagination (50 items/page)
- NFR3.3: Receipt OCR completes in <30 seconds
- NFR3.4: Import 10,000 transactions in <60 seconds

#### NFR4: Usability
- NFR4.1: Responsive design (desktop-first)
- NFR4.2: English UI with German financial terms in brackets
- NFR4.3: Keyboard navigation support
- NFR4.4: Clear error messages

## Technical Architecture

### System Components

```
┌─────────────────────────────────────────────────────────────────────────┐
│                           Host Machine (Pop!_OS)                        │
│  ┌───────────────────────────────────────────────────────────────────┐  │
│  │                        Docker Compose                              │  │
│  │  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  ┌───────────┐ │  │
│  │  │   nginx     │  │   Next.js   │  │   FastAPI   │  │  Ollama   │ │  │
│  │  │  (reverse   │  │  Frontend   │  │   Backend   │  │  (GPU)    │ │  │
│  │  │   proxy)    │  │   :3000     │  │   :8000     │  │  :11434   │ │  │
│  │  └──────┬──────┘  └──────┬──────┘  └──────┬──────┘  └─────┬─────┘ │  │
│  │         │                │                │                │       │  │
│  │         │                └────────────────┼────────────────┘       │  │
│  │         │                                 │                        │  │
│  │         │                          ┌──────▼──────┐                 │  │
│  │         │                          │ PostgreSQL  │                 │  │
│  │         │                          │   :5432     │                 │  │
│  │         │                          └──────┬──────┘                 │  │
│  │         │                                 │                        │  │
│  └─────────┼─────────────────────────────────┼────────────────────────┘  │
│            │                                 │                           │
│     ┌──────▼──────┐                   ┌──────▼──────┐                    │
│     │   Browser   │                   │   Named     │                    │
│     │  :80/:443   │                   │   Volumes   │                    │
│     └─────────────┘                   │  (persist)  │                    │
│                                       └─────────────┘                    │
└─────────────────────────────────────────────────────────────────────────┘
```

### Data Flow

```
User Action                    Frontend              Backend                AI/DB
     │                            │                     │                     │
     │  Upload Receipt            │                     │                     │
     ├───────────────────────────►│                     │                     │
     │                            │  POST /receipts     │                     │
     │                            ├────────────────────►│                     │
     │                            │                     │  Store image        │
     │                            │                     ├────────────────────►│
     │                            │                     │                     │
     │                            │                     │  OCR via Ollama     │
     │                            │                     ├────────────────────►│
     │                            │                     │◄────────────────────┤
     │                            │                     │                     │
     │                            │                     │  Save to DB         │
     │                            │                     ├────────────────────►│
     │                            │  JSON response      │                     │
     │                            │◄────────────────────┤                     │
     │  Display extracted data    │                     │                     │
     │◄───────────────────────────┤                     │                     │
```

### Database Schema

```sql
-- Users table
CREATE TABLE users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    username VARCHAR(50) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Accounts (bank accounts)
CREATE TABLE accounts (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    name VARCHAR(100) NOT NULL,
    iban_last4 VARCHAR(4),
    account_type VARCHAR(20) DEFAULT 'checking',
    currency VARCHAR(3) DEFAULT 'EUR',
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Categories (hierarchical)
CREATE TABLE categories (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(50) NOT NULL,
    name_de VARCHAR(50),
    parent_id UUID REFERENCES categories(id),
    is_income BOOLEAN DEFAULT false,
    icon VARCHAR(50),
    color VARCHAR(7),
    sort_order INT DEFAULT 0,
    UNIQUE(name, parent_id)
);

-- Tax categories (German specific)
CREATE TABLE tax_categories (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(50) NOT NULL UNIQUE,
    name_de VARCHAR(50) NOT NULL,
    anlage VARCHAR(50),
    description TEXT,
    deductible_percent INT DEFAULT 100
);

-- Transactions
CREATE TABLE transactions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    account_id UUID REFERENCES accounts(id),
    
    -- Core fields
    date DATE NOT NULL,
    amount DECIMAL(12,2) NOT NULL,
    currency VARCHAR(3) DEFAULT 'EUR',
    
    -- Counterparty
    counterparty VARCHAR(255),
    counterparty_iban VARCHAR(34),
    
    -- Description
    description TEXT,
    e_ref VARCHAR(100),
    mandate_ref VARCHAR(100),
    creditor_id VARCHAR(100),
    
    -- Categorization
    category_id UUID REFERENCES categories(id),
    subcategory_id UUID REFERENCES categories(id),
    tax_category_id UUID REFERENCES tax_categories(id),
    
    -- Finanzguru metadata
    fg_contract VARCHAR(100),
    fg_contract_frequency VARCHAR(20),
    fg_contract_id VARCHAR(50),
    fg_is_transfer BOOLEAN DEFAULT false,
    fg_excluded_from_budget BOOLEAN DEFAULT false,
    fg_transaction_type VARCHAR(50),
    
    -- User additions
    tags TEXT[],
    notes TEXT,
    
    -- Import tracking
    source VARCHAR(20) DEFAULT 'manual',
    import_hash VARCHAR(64),
    
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    
    UNIQUE(import_hash)
);

-- Receipts
CREATE TABLE receipts (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    transaction_id UUID REFERENCES transactions(id),
    
    -- File storage
    original_filename VARCHAR(255),
    stored_path VARCHAR(500) NOT NULL,
    file_size INT,
    mime_type VARCHAR(50),
    
    -- OCR results
    ocr_raw_text TEXT,
    ocr_model VARCHAR(50),
    ocr_processed_at TIMESTAMPTZ,
    
    -- Extracted data (JSON)
    extracted_data JSONB,
    
    -- Status
    status VARCHAR(20) DEFAULT 'pending',
    error_message TEXT,
    
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Budgets
CREATE TABLE budgets (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    category_id UUID REFERENCES categories(id),
    
    amount DECIMAL(12,2) NOT NULL,
    period VARCHAR(10) DEFAULT 'monthly',
    start_date DATE NOT NULL,
    end_date DATE,
    
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Category rules (auto-categorization)
CREATE TABLE category_rules (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    
    -- Match conditions
    counterparty_contains VARCHAR(255),
    description_contains VARCHAR(255),
    amount_min DECIMAL(12,2),
    amount_max DECIMAL(12,2),
    
    -- Assign
    category_id UUID REFERENCES categories(id),
    tax_category_id UUID REFERENCES tax_categories(id),
    
    priority INT DEFAULT 0,
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Indexes for performance
CREATE INDEX idx_transactions_user_date ON transactions(user_id, date DESC);
CREATE INDEX idx_transactions_category ON transactions(category_id);
CREATE INDEX idx_transactions_import_hash ON transactions(import_hash);
CREATE INDEX idx_receipts_user ON receipts(user_id);
CREATE INDEX idx_budgets_user_category ON budgets(user_id, category_id);
```

### API Endpoints

#### Authentication
```
POST   /api/auth/register     Register new user
POST   /api/auth/login        Login, returns JWT
POST   /api/auth/logout       Invalidate token
GET    /api/auth/me           Get current user
```

#### Transactions
```
GET    /api/transactions              List (paginated, filterable)
GET    /api/transactions/:id          Get single
POST   /api/transactions              Create manual
PUT    /api/transactions/:id          Update
DELETE /api/transactions/:id          Delete
POST   /api/transactions/import       Import from XLSX
GET    /api/transactions/stats        Aggregated statistics
```

#### Receipts
```
GET    /api/receipts                  List user's receipts
GET    /api/receipts/:id              Get single with OCR data
POST   /api/receipts                  Upload and process
PUT    /api/receipts/:id              Update (link to transaction)
DELETE /api/receipts/:id              Delete receipt
GET    /api/receipts/:id/image        Get original image
POST   /api/receipts/:id/reprocess    Re-run OCR
```

#### Categories
```
GET    /api/categories                List all categories
POST   /api/categories                Create custom
PUT    /api/categories/:id            Update
DELETE /api/categories/:id            Delete (if unused)
GET    /api/categories/tax            List tax categories
```

#### Budgets
```
GET    /api/budgets                   List user's budgets
POST   /api/budgets                   Create
PUT    /api/budgets/:id               Update
DELETE /api/budgets/:id               Delete
GET    /api/budgets/summary           Current period summary
```

#### AI Assistant
```
POST   /api/ai/chat                   Natural language query
POST   /api/ai/categorize             Suggest category for transaction
POST   /api/ai/insights               Get spending insights
```

#### Analytics
```
GET    /api/analytics/monthly         Monthly breakdown
GET    /api/analytics/categories      Category spending
GET    /api/analytics/trends          Trend analysis
GET    /api/analytics/tax-summary     Tax-relevant summary
```

### Security Considerations

1. **Authentication**
   - Passwords hashed with bcrypt (cost factor 12)
   - JWT with 24-hour expiry, refresh token with 7-day expiry
   - Tokens stored in httpOnly cookies (not localStorage)

2. **Input Validation**
   - All inputs validated with Pydantic (backend) and Zod (frontend)
   - File uploads: max 10MB, allowed types only
   - SQL injection prevented via SQLAlchemy ORM

3. **Data Protection**
   - All data local (no external APIs for user data)
   - Database in Docker with non-root user
   - Uploaded files stored outside webroot

## UI/UX Design

### Layout Structure
```
┌─────────────────────────────────────────────────────────────────┐
│  Logo        Dashboard  Transactions  Receipts  Budgets    User │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │                    Page Content                          │   │
│  │                                                         │   │
│  │  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐     │   │
│  │  │   Card 1    │  │   Card 2    │  │   Card 3    │     │   │
│  │  │             │  │             │  │             │     │   │
│  │  └─────────────┘  └─────────────┘  └─────────────┘     │   │
│  │                                                         │   │
│  │  ┌─────────────────────────────────────────────────┐   │   │
│  │  │              Main Content Area                   │   │   │
│  │  │                                                 │   │   │
│  │  │                                                 │   │   │
│  │  └─────────────────────────────────────────────────┘   │   │
│  │                                                         │   │
│  └─────────────────────────────────────────────────────────┘   │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

### Color Scheme
- Primary: Blue (#2563EB) - Trust, finance
- Success: Green (#16A34A) - Income, positive
- Danger: Red (#DC2626) - Expenses, warnings
- Neutral: Slate grays
- Background: White/Slate-50

### Key Screens

1. **Dashboard**
   - Monthly summary cards (income, expenses, balance)
   - Spending by category (donut chart)
   - Recent transactions list
   - Budget progress bars

2. **Transactions**
   - Filterable table with pagination
   - Quick category assignment
   - Bulk actions
   - Import button

3. **Receipts**
   - Grid view of receipt thumbnails
   - Upload dropzone
   - OCR result preview
   - Link to transaction modal

4. **Budgets**
   - Category budget list
   - Progress visualization
   - AI recommendations panel

## Testing Strategy

### Unit Tests
- Backend: pytest with fixtures
- Frontend: Vitest + React Testing Library
- Coverage target: 80% on business logic

### Integration Tests
- API endpoint tests with test database
- Frontend component integration

### E2E Tests (Playwright)
- Critical flows only:
  1. User registration and login
  2. Import Finanzguru data
  3. Upload and process receipt
  4. View dashboard
  5. Set budget

### Test Data
- Fixtures for common scenarios
- Anonymized sample Finanzguru export
- Sample receipt images

## Deployment

### Development
```bash
docker compose -f docker-compose.dev.yml up
```

### Production (local)
```bash
docker compose up -d
```

### Backup Strategy
```bash
# Backup database
docker exec finanzpilot-postgres pg_dump -U finanzpilot finanzpilot > backup.sql

# Backup uploads
tar -czf uploads_backup.tar.gz ./uploads/
```

## Future Considerations (Out of Scope for MVP)

- Multi-user support (family sharing)
- Mobile app (React Native)
- Bank API integration (FinTS/HBCI)
- Investment tracking
- Multi-currency support
- Export to tax software (ELSTER)
- Encrypted database at rest
