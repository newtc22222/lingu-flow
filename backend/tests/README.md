# Backend tests

## Fast suite (default)

SQLite in-memory. Foreign keys are enabled via `PRAGMA foreign_keys=ON` (still not full Postgres parity).

```bash
cd backend
./venv/Scripts/python.exe -m pytest -q
```

Postgres-marked tests are **collected** but **skip** when Postgres is unreachable, so a machine without Docker still gets a green default run.
## Postgres integrity suite (`@pytest.mark.postgres`)

Covers cascade/FK behavior and real commit boundaries (F-08 / issue #47).
Tests live under `tests/postgres/`. Schema is applied with **Alembic `upgrade head`**, not `create_all`.

### Prerequisites

1. A reachable Postgres (local install or Docker Compose `postgres` service).
2. Credentials that can create a database (or a pre-created `linguflow_test` DB).

Default URL (matches `docker-compose.yml` user/password):

```text
postgresql+asyncpg://postgres:postgres@127.0.0.1:5432/linguflow_test
```

Override with `POSTGRES_TEST_URL` if needed. The suite creates `linguflow_test` when missing, then drops/recreates the `public` schema for a clean Alembic run.

### Run

```bash
cd backend

# With Docker Compose Postgres on the host-mapped port:
#   docker compose up -d postgres
$env:POSTGRES_TEST_URL = "postgresql+asyncpg://postgres:postgres@127.0.0.1:5432/linguflow_test"  # PowerShell
./venv/Scripts/python.exe -m pytest -m postgres -q
```

Bash:

```bash
export POSTGRES_TEST_URL=postgresql+asyncpg://postgres:postgres@127.0.0.1:5432/linguflow_test
./venv/bin/python -m pytest -m postgres -q
```

If Postgres is unreachable, the suite **skips** rather than hard-failing (so local machines without Docker stay green on the default suite).

### What is asserted

| Test | Intent |
|------|--------|
| `test_seed_key_unique_constraint` | Unique `seed_key` index |
| `test_soft_delete_keeps_answer_history_resolvable` | Soft-delete does not erase answer history |
| `test_delete_template_removes_links_not_questions` | Template delete drops junction only |
| `test_create_session_is_atomic_under_midway_failure` | Dual-commit orphan probe — **xfail until A5 / #48** |

## CI

GitHub Actions workflow `.github/workflows/backend-tests.yml`:

1. Always runs the SQLite suite.
2. Runs the Postgres suite against a service container.
