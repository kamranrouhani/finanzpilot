# Testing Rules

## TDD Approach (Test-Driven Development)
1. Write failing test first
2. Implement minimum code to pass
3. Refactor if needed
4. Repeat

## Backend Testing (pytest)

### File Naming
```
tests/
├── conftest.py          # Shared fixtures
├── test_auth.py         # Feature tests
├── test_transactions.py
├── unit/                # Pure unit tests
│   └── test_utils.py
└── integration/         # Integration tests
    └── test_api.py
```

### Test Structure
```python
def test_should_describe_expected_behavior():
    # Arrange
    user = create_test_user()
    
    # Act
    result = login(user.username, user.password)
    
    # Assert
    assert result.token is not None
```

### Fixtures
```python
@pytest.fixture
def db_session():
    """Fresh database session for each test."""
    # Setup
    yield session
    # Teardown

@pytest.fixture
def authenticated_client(db_session):
    """Client with valid auth token."""
    pass
```

### Mocking Ollama
```python
@pytest.fixture
def mock_ollama(mocker):
    return mocker.patch(
        'app.features.ai.service.ollama_client.chat',
        return_value={'message': {'content': '{"category": "Food"}'}}
    )
```

## Frontend Testing (Vitest + RTL)

### File Naming
```
tests/
├── components/
│   ├── auth.test.tsx
│   └── transactions.test.tsx
├── hooks/
│   └── useAuth.test.ts
└── utils/
    └── formatters.test.ts
```

### Component Test Structure
```typescript
describe('LoginForm', () => {
  it('should show error on invalid credentials', async () => {
    // Arrange
    render(<LoginForm />);
    
    // Act
    await userEvent.type(screen.getByLabelText('Username'), 'test');
    await userEvent.type(screen.getByLabelText('Password'), 'wrong');
    await userEvent.click(screen.getByRole('button', { name: /login/i }));
    
    // Assert
    expect(await screen.findByText(/invalid/i)).toBeInTheDocument();
  });
});
```

### API Mocking
```typescript
import { rest } from 'msw';
import { setupServer } from 'msw/node';

const server = setupServer(
  rest.post('/api/auth/login', (req, res, ctx) => {
    return res(ctx.json({ token: 'test-token' }));
  })
);

beforeAll(() => server.listen());
afterEach(() => server.resetHandlers());
afterAll(() => server.close());
```

## E2E Testing (Playwright)

### Test Only Critical Flows
1. User registration and login
2. Import Finanzguru data
3. Upload receipt and view OCR result
4. Create and track budget
5. Use chat feature

### Page Object Pattern
```typescript
class LoginPage {
  constructor(private page: Page) {}
  
  async login(username: string, password: string) {
    await this.page.fill('[name=username]', username);
    await this.page.fill('[name=password]', password);
    await this.page.click('button[type=submit]');
  }
}
```

## Coverage Requirements
- Backend business logic: >80%
- Frontend components: >70%
- E2E: Cover all critical user journeys

## Running Tests
```bash
# All tests
make test

# Backend only
make test-backend

# Frontend only  
make test-frontend

# E2E only
make test-e2e

# With coverage
make test-coverage
```
