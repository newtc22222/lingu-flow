"""Postgres-only fixtures for @pytest.mark.postgres tests.

Imported by test_postgres_integrity.py. Not required by the SQLite suite.
Uses only function-scoped async fixtures so pytest-asyncio loop scopes stay
compatible with asyncio_default_fixture_loop_scope = function.
"""
from __future__ import annotations

import os
import uuid
from pathlib import Path
from typing import AsyncGenerator
from urllib.parse import urlparse, urlunparse

import pytest
import pytest_asyncio
from alembic import command
from alembic.config import Config
from httpx import ASGITransport, AsyncClient
from sqlalchemy import text
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from app.config import get_settings
from app.database import get_db
from app.main import app

DEFAULT_POSTGRES_TEST_URL = (
    "postgresql+asyncpg://postgres:postgres@127.0.0.1:5432/linguflow_test"
)

# Module-level: Alembic upgrade once per process when the first postgres test runs.
_MIGRATIONS_READY = False
_SKIP_REASON: str | None = None


def _normalize_async_url(url: str) -> str:
    url = url.strip()
    if url.startswith("postgresql://"):
        return url.replace("postgresql://", "postgresql+asyncpg://", 1)
    return url


def _admin_url(async_url: str) -> str:
    parsed = urlparse(async_url)
    return urlunparse(parsed._replace(path="/postgres"))


def _db_name(async_url: str) -> str:
    parsed = urlparse(async_url)
    name = parsed.path.lstrip("/")
    if not name:
        raise ValueError(f"POSTGRES_TEST_URL has no database name: {async_url}")
    return name


def _backend_root() -> Path:
    return Path(__file__).resolve().parents[1]


def _run_alembic_upgrade(async_url: str) -> None:
    os.environ["DATABASE_URL"] = async_url
    get_settings.cache_clear()
    cfg = Config(str(_backend_root() / "alembic.ini"))
    cfg.set_main_option("sqlalchemy.url", async_url)
    cwd = os.getcwd()
    try:
        os.chdir(_backend_root())
        command.upgrade(cfg, "head")
    finally:
        os.chdir(cwd)
        get_settings.cache_clear()


async def _prepare_database(async_url: str) -> None:
    """Create DB if needed, reset public schema, run Alembic (once per process)."""
    global _MIGRATIONS_READY, _SKIP_REASON
    if _MIGRATIONS_READY:
        return
    if _SKIP_REASON:
        pytest.skip(_SKIP_REASON)

    try:
        admin = create_async_engine(_admin_url(async_url), isolation_level="AUTOCOMMIT")
        try:
            async with admin.connect() as conn:
                name = _db_name(async_url)
                exists = (
                    await conn.execute(
                        text("SELECT 1 FROM pg_database WHERE datname = :n"),
                        {"n": name},
                    )
                ).scalar()
                if not exists:
                    await conn.execute(text(f'CREATE DATABASE "{name}"'))
        finally:
            await admin.dispose()

        bootstrap = create_async_engine(async_url, isolation_level="AUTOCOMMIT")
        try:
            async with bootstrap.connect() as conn:
                await conn.execute(text("DROP SCHEMA IF EXISTS public CASCADE"))
                await conn.execute(text("CREATE SCHEMA public"))
                await conn.execute(text("GRANT ALL ON SCHEMA public TO public"))
        finally:
            await bootstrap.dispose()

        _run_alembic_upgrade(async_url)
        _MIGRATIONS_READY = True
    except Exception as exc:  # noqa: BLE001
        _SKIP_REASON = f"Postgres not available for integration tests: {exc}"
        pytest.skip(_SKIP_REASON)


@pytest.fixture
def postgres_url() -> str:
    return _normalize_async_url(
        os.getenv("POSTGRES_TEST_URL", DEFAULT_POSTGRES_TEST_URL)
    )


@pytest_asyncio.fixture
async def pg_engine(postgres_url: str) -> AsyncGenerator[AsyncEngine, None]:
    await _prepare_database(postgres_url)
    engine = create_async_engine(postgres_url, echo=False, pool_pre_ping=True)
    try:
        async with engine.connect() as conn:
            await conn.execute(text("SELECT 1"))
    except Exception as exc:  # noqa: BLE001
        await engine.dispose()
        pytest.skip(f"Postgres not available for integration tests: {exc}")
    yield engine
    await engine.dispose()


@pytest_asyncio.fixture
async def pg_session(pg_engine: AsyncEngine) -> AsyncGenerator[AsyncSession, None]:
    """
    Per-test session with production-like commit on success and TRUNCATE cleanup.

    Real commits must stick (cascade / dual-commit probes); isolation is via
    truncate, not outer-transaction rollback.
    """
    Session = async_sessionmaker(
        bind=pg_engine,
        class_=AsyncSession,
        expire_on_commit=False,
        autocommit=False,
        autoflush=False,
    )
    async with Session() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            try:
                await session.rollback()
                await session.execute(
                    text(
                        """
                        TRUNCATE TABLE
                            answer_records,
                            exam_sessions,
                            exam_template_questions,
                            questions,
                            exam_templates,
                            cards,
                            decks,
                            user_settings,
                            users
                        RESTART IDENTITY CASCADE
                        """
                    )
                )
                await session.commit()
            except Exception:
                await session.rollback()


@pytest_asyncio.fixture
async def pg_client(pg_session: AsyncSession) -> AsyncGenerator[AsyncClient, None]:
    async def _override_get_db():
        try:
            yield pg_session
            await pg_session.commit()
        except Exception:
            await pg_session.rollback()
            raise

    app.dependency_overrides[get_db] = _override_get_db
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://testserver"
    ) as ac:
        yield ac
    app.dependency_overrides.clear()


def unique_name(prefix: str) -> str:
    return f"{prefix}_{uuid.uuid4().hex[:10]}"
