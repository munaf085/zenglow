# Zenglow — Git Workflow

## Branch Strategy

We use a simplified **GitHub Flow**:

```
main          ← production-ready, protected
  └── develop ← integration branch (optional for larger teams)
       └── feature/...   ← feature branches
       └── fix/...       ← bug fix branches
       └── chore/...     ← infrastructure, deps, tooling
```

For a small team, branches merge directly to `main` via pull request.

---

## Branch Naming

```
feature/booking-engine-availability
feature/admin-subscription-plans
fix/double-booking-race-condition
fix/auth-refresh-token-rotation
chore/upgrade-fastapi-0.111
chore/add-celery-beat-schedule
docs/update-deployment-guide
```

---

## Commit Messages

Follow [Conventional Commits](https://www.conventionalcommits.org/):

```
<type>(<scope>): <short description>

[optional body]

[optional footer: Closes #123]
```

### Types

| Type | When to use |
|---|---|
| `feat` | New feature or API endpoint |
| `fix` | Bug fix |
| `chore` | Build, deps, tooling (no production code change) |
| `docs` | Documentation only |
| `refactor` | Code change that neither fixes a bug nor adds a feature |
| `test` | Adding or updating tests |
| `perf` | Performance improvement |
| `ci` | CI/CD configuration |

### Examples

```
feat(booking): add Redis slot locking to prevent double-booking

fix(auth): correct refresh token hash comparison in logout

chore(deps): upgrade SQLAlchemy to 2.0.30

test(tenant): add cross-tenant service access test

docs(api): document payment webhook verification flow
```

---

## Pull Request Process

1. **Branch** off `main`:
   ```bash
   git checkout main
   git pull origin main
   git checkout -b feature/my-feature
   ```

2. **Develop** your feature with small, focused commits

3. **Test locally** before pushing:
   ```bash
   # Backend
   pytest tests/ -x

   # Frontend
   pnpm type-check
   pnpm lint
   pnpm test
   ```

4. **Push** and open a PR:
   ```bash
   git push -u origin feature/my-feature
   # Open PR on GitHub
   ```

5. **PR requirements** before merge:
   - All CI checks pass (lint, type-check, tests, Docker build)
   - At least 1 reviewer approval
   - No unresolved review comments
   - Tenant isolation tests pass

6. **Merge** using **Squash and Merge** for a clean history, or **Rebase and Merge** when the commit history is meaningful

7. **Delete** the branch after merge

---

## Protected Branch Rules (`main`)

- Require pull request before merging
- Require status checks to pass (CI workflow)
- Require linear history
- No force-pushes
- No direct commits

---

## Release Tagging

```bash
# After merging to main, tag a release
git checkout main
git pull
git tag -a v1.2.0 -m "Release v1.2.0: Add booking engine availability"
git push origin v1.2.0
```

This triggers the `deploy.yml` workflow which builds and pushes Docker images tagged with the version.

---

## Hotfix Process

For urgent production fixes:

```bash
git checkout main
git pull
git checkout -b fix/critical-payment-bug

# Fix, test, commit
git push -u origin fix/critical-payment-bug

# Open expedited PR — requires 1 approval + all CI checks
# After merge, tag immediately
git tag -a v1.2.1 -m "Hotfix: critical payment signature bug"
git push origin v1.2.1
```

---

## What NOT to Commit

- `.env` files with real secrets
- `node_modules/`, `.venv/`, `__pycache__/`
- Build outputs (`.next/`, `dist/`)
- Database files, upload directories
- IDE settings (`.idea/`, `.vscode/`)
- Private keys, certificates

These are all listed in `.gitignore`.
