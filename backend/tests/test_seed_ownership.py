"""A6 / F-06: seed is entrypoint-owned, not multi-worker lifespan."""
from __future__ import annotations

import inspect
from pathlib import Path

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.main import lifespan
from app.seed import exam_seed
from app.seed.exam_seed import (
    SEED_ADVISORY_LOCK_KEY,
    _acquire_seed_lock,
    _release_seed_lock,
    seed_builtin_exams,
)


def test_entrypoint_runs_seed_after_migrate():
    """Container start path: alembic → python -m seed → uvicorn."""
    entry = Path(__file__).resolve().parents[1] / "entrypoint.sh"
    # Ignore comment lines so the word "uvicorn" in a comment cannot reorder checks.
    lines = [
        ln.strip()
        for ln in entry.read_text(encoding="utf-8").splitlines()
        if ln.strip() and not ln.strip().startswith("#")
    ]
    joined = "\n".join(lines)
    assert "alembic upgrade head" in joined
    assert "python -m app.seed.exam_seed" in joined
    assert any(ln.startswith("exec uvicorn") or ln.startswith("uvicorn") for ln in lines)
    assert joined.index("alembic upgrade head") < joined.index("python -m app.seed.exam_seed")
    assert joined.index("python -m app.seed.exam_seed") < joined.index("uvicorn")


def test_lifespan_does_not_call_seed():
    """API workers must not re-seed on every process start."""
    source = inspect.getsource(lifespan)
    assert "seed_builtin_exams" not in source
    assert "entrypoint" in source.lower() or "seed" in source.lower()


def test_seed_module_exposes_cli_and_lock_key():
    assert hasattr(exam_seed, "run_seed_cli")
    assert isinstance(SEED_ADVISORY_LOCK_KEY, int)
    assert "pg_advisory_lock" in Path(exam_seed.__file__).read_text(encoding="utf-8")


@pytest.mark.asyncio
async def test_advisory_lock_is_noop_on_sqlite(db_session: AsyncSession):
    """SQLite tests must keep working without Postgres lock primitives."""
    held = await _acquire_seed_lock(db_session)
    assert held is False
    await _release_seed_lock(db_session, held)


@pytest.mark.asyncio
async def test_seed_builtin_exams_still_idempotent(db_session: AsyncSession):
    """Seeder remains callable from tests / CLI without lifespan."""
    await seed_builtin_exams(db_session)
    await seed_builtin_exams(db_session)
