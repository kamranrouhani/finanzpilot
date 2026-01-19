# Git Workflow Rules

## Branch Strategy
- `main` - Production-ready code only
- `feature/<phase>-<name>` - Feature development
- Never commit directly to main

## Commit Messages (Conventional Commits)
```
feat: add user authentication
fix: resolve JWT token expiry issue
docs: update API documentation
test: add transaction import tests
chore: update dependencies
refactor: simplify budget calculation
style: format code with black/prettier
```

## Commit Frequency
- Commit after each working feature
- Commit message should describe WHAT, not HOW
- Keep commits atomic (one logical change)

## Before Every Commit
1. Run tests: `make test`
2. Run linting: `make lint`
3. Check for uncommitted files: `git status`
4. Review changes: `git diff --staged`

## Pull Request Checklist
- [ ] All tests pass locally
- [ ] No linting errors
- [ ] Documentation updated if needed
- [ ] Commit messages follow convention
- [ ] PR description explains changes

## Branch Naming
```
feature/phase-1          # Phase work
feature/auth-jwt         # Specific feature
fix/receipt-upload-error # Bug fix
docs/api-endpoints       # Documentation
```

## Merge Strategy
- Squash merge for feature branches
- Keep commit history clean on main
