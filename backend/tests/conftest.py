from typing import AsyncGenerator
import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy import event
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.database import Base, get_db
from app.main import app
from app.models import User, Deck, Card, ExamTemplate, Question, ExamSession, AnswerRecord, UserSettings  # Register all models  # noqa: F401

TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"

test_engine = create_async_engine(
    TEST_DATABASE_URL,
    echo=False,
    future=True,
)

# SQLite disables FK enforcement by default. Enabling it is still not full
# Postgres parity (dialects, types, concurrent locks differ), but it catches
# the cheapest cascade mistakes in the fast suite. Postgres-marked tests under
# tests/postgres/ are the real integrity gate.
@event.listens_for(test_engine.sync_engine, "connect")
def _sqlite_enable_foreign_keys(dbapi_connection, connection_record):
    cursor = dbapi_connection.cursor()
    cursor.execute("PRAGMA foreign_keys=ON")
    cursor.close()

TestingSessionLocal = async_sessionmaker(
    bind=test_engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False,
)


@pytest_asyncio.fixture(scope="function")
async def db_session() -> AsyncGenerator[AsyncSession, None]:
    """Fixture that creates database tables in SQLite in-memory and yields a clean AsyncSession per test."""
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async with TestingSessionLocal() as session:
        yield session

    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


@pytest_asyncio.fixture(scope="function")
async def client(db_session: AsyncSession) -> AsyncGenerator[AsyncClient, None]:
    """Fixture that yields an AsyncClient configured with test DB dependency override.

    Note: this override yields the session without the production get_db()
    commit/rollback wrapper. HTTP-path transaction ownership is covered by the
    @pytest.mark.postgres suite (see tests/README.md).
    """
    async def _override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = _override_get_db

    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://testserver"
    ) as ac:
        yield ac

    app.dependency_overrides.clear()
