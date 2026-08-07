import uuid
from datetime import timedelta

import pytest
from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import _touch_last_active
from app.core.timeutils import utcnow
from app.models import Card, Deck, ExamSession, ExamTemplate, User
from app.services.guest_service import cleanup_inactive_guests


async def _make_guest(db: AsyncSession, *, idle_days: float = 0.0) -> User:
    """Insert a guest whose last_active is `idle_days` in the past."""
    guest = User(is_guest=True, last_active=utcnow() - timedelta(days=idle_days))
    db.add(guest)
    await db.commit()
    await db.refresh(guest)
    return guest


async def _make_template(
    db: AsyncSession, owner: User, *, is_public: bool = False
) -> ExamTemplate:
    template = ExamTemplate(
        user_id=owner.id,
        name="Guest Custom Exam",
        exam_type="custom",
        duration_minutes=30,
        is_public=is_public,
    )
    db.add(template)
    await db.commit()
    await db.refresh(template)
    return template


# ─── identity ────────────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_guest_token_resumes_same_account_and_records_ip(
    client: AsyncClient, db_session: AsyncSession
):
    """The browser's token — not its IP — is what resumes a guest session."""
    first = await client.post(
        "/api/auth/guest", headers={"X-Forwarded-For": "203.0.113.7, 10.0.0.1"}
    )
    assert first.status_code == 201
    guest_token = first.json()["token"]
    guest_id = first.json()["user"]["id"]

    stored = await db_session.get(User, uuid.UUID(guest_id))
    assert stored is not None
    # Left-most XFF entry is the client; the proxy hop is discarded.
    assert stored.last_ip == "203.0.113.7"

    # Same token from a completely different address still resumes the account.
    second = await client.post(
        "/api/auth/guest",
        json={"guestToken": guest_token},
        headers={"X-Forwarded-For": "198.51.100.42"},
    )
    assert second.status_code == 201
    assert second.json()["user"]["id"] == guest_id

    await db_session.refresh(stored)
    assert stored.last_ip == "198.51.100.42"


@pytest.mark.asyncio
async def test_guest_without_token_gets_a_separate_account(client: AsyncClient):
    """Two browsers sharing one IP must not share a guest account."""
    shared_ip = {"X-Forwarded-For": "203.0.113.7"}
    first = await client.post("/api/auth/guest", headers=shared_ip)
    second = await client.post("/api/auth/guest", headers=shared_ip)

    assert first.json()["user"]["id"] != second.json()["user"]["id"]


# ─── cleanup on login ────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_login_to_existing_account_deletes_the_guest(
    client: AsyncClient, db_session: AsyncSession
):
    reg = await client.post(
        "/api/auth/register",
        json={
            "username": "returning",
            "email": "returning@linguflow.com",
            "password": "Password123!",
        },
    )
    account_id = uuid.UUID(reg.json()["user"]["id"])

    guest_res = await client.post("/api/auth/guest")
    guest_token = guest_res.json()["token"]
    guest_id = uuid.UUID(guest_res.json()["user"]["id"])

    deck = Deck(user_id=guest_id, name="Throwaway Deck")
    db_session.add(deck)
    await db_session.commit()
    card = Card(user_id=guest_id, deck_id=deck.id, front="a", back="b")
    db_session.add(card)
    await db_session.commit()
    deck_id, card_id = deck.id, card.id

    login = await client.post(
        "/api/auth/login",
        json={
            "email": "returning@linguflow.com",
            "password": "Password123!",
            "guestToken": guest_token,
        },
    )
    assert login.status_code == 200
    assert login.json()["user"]["id"] == str(account_id)

    db_session.expire_all()
    assert await db_session.get(User, guest_id) is None
    assert await db_session.get(Deck, deck_id) is None
    assert await db_session.get(Card, card_id) is None
    # The account that was logged into is untouched.
    assert await db_session.get(User, account_id) is not None


@pytest.mark.asyncio
async def test_login_without_guest_token_deletes_nothing(
    client: AsyncClient, db_session: AsyncSession
):
    await client.post(
        "/api/auth/register",
        json={
            "username": "plain",
            "email": "plain@linguflow.com",
            "password": "Password123!",
        },
    )
    guest_id = (await _make_guest(db_session)).id

    login = await client.post(
        "/api/auth/login",
        json={"email": "plain@linguflow.com", "password": "Password123!"},
    )
    assert login.status_code == 200

    db_session.expire_all()
    assert await db_session.get(User, guest_id) is not None


# ─── inactivity sweep ────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_sweep_removes_only_stale_guests(db_session: AsyncSession):
    stale_id = (await _make_guest(db_session, idle_days=8)).id
    recent_id = (await _make_guest(db_session, idle_days=2)).id

    # A registered account idle for a month must never be touched.
    veteran = User(
        username="veteran",
        email="veteran@linguflow.com",
        password_hash="x",
        is_guest=False,
        last_active=utcnow() - timedelta(days=30),
    )
    db_session.add(veteran)
    await db_session.commit()
    await db_session.refresh(veteran)
    veteran_id = veteran.id

    removed = await cleanup_inactive_guests(db_session)
    assert removed == 1

    db_session.expire_all()
    assert await db_session.get(User, stale_id) is None
    assert await db_session.get(User, recent_id) is not None
    assert await db_session.get(User, veteran_id) is not None


@pytest.mark.asyncio
async def test_sweep_cascades_guest_owned_data(db_session: AsyncSession):
    guest = await _make_guest(db_session, idle_days=10)
    deck = Deck(user_id=guest.id, name="Stale Deck")
    db_session.add(deck)
    await db_session.commit()
    deck_id = deck.id

    assert await cleanup_inactive_guests(db_session) == 1

    db_session.expire_all()
    assert await db_session.get(Deck, deck_id) is None


@pytest.mark.asyncio
async def test_sweep_does_not_leave_a_public_template_masquerading_as_builtin(
    db_session: AsyncSession,
):
    """user_id is ON DELETE SET NULL, and an ownerless public template reads as
    a seeded built-in — so the guest's template must go, not just lose its owner."""
    guest = await _make_guest(db_session, idle_days=9)
    template = await _make_template(db_session, guest, is_public=True)
    template_id = template.id

    assert await cleanup_inactive_guests(db_session) == 1

    db_session.expire_all()
    assert await db_session.get(ExamTemplate, template_id) is None


@pytest.mark.asyncio
async def test_sweep_preserves_a_template_another_user_has_sat(
    db_session: AsyncSession,
):
    """Hard-deleting it would cascade away someone else's finished session."""
    guest = await _make_guest(db_session, idle_days=9)
    template = await _make_template(db_session, guest, is_public=True)

    other = User(
        username="other",
        email="other@linguflow.com",
        password_hash="x",
        is_guest=False,
    )
    db_session.add(other)
    await db_session.commit()
    await db_session.refresh(other)

    session = ExamSession(
        user_id=other.id,
        exam_template_id=template.id,
        time_limit_minutes=30,
        status="completed",
    )
    db_session.add(session)
    await db_session.commit()
    template_id, session_id = template.id, session.id

    assert await cleanup_inactive_guests(db_session) == 1

    db_session.expire_all()
    surviving = await db_session.get(ExamTemplate, template_id)
    assert surviving is not None
    assert surviving.user_id is None
    # Unpublished, so it cannot be mistaken for a built-in in the exam hub.
    assert surviving.is_public is False
    assert await db_session.get(ExamSession, session_id) is not None


@pytest.mark.asyncio
async def test_sweep_handles_more_guests_than_one_batch(db_session: AsyncSession):
    for _ in range(5):
        await _make_guest(db_session, idle_days=9)

    assert await cleanup_inactive_guests(db_session, batch_size=2) == 5

    remaining = await db_session.execute(select(User).where(User.is_guest.is_(True)))
    assert remaining.scalars().all() == []


# ─── activity tracking ───────────────────────────────────────────────────────


def test_touch_last_active_is_throttled():
    """Every authenticated request passes through here; only stale values write."""
    fresh = User(is_guest=True, last_active=utcnow() - timedelta(minutes=1))
    before = fresh.last_active
    _touch_last_active(fresh)
    assert fresh.last_active == before

    stale = User(is_guest=True, last_active=utcnow() - timedelta(hours=3))
    _touch_last_active(stale)
    assert utcnow() - stale.last_active < timedelta(seconds=5)


def test_touch_last_active_handles_naive_timestamps():
    """SQLite hands back naive datetimes; mixing them with an aware now() raises."""
    naive = User(is_guest=True)
    naive.last_active = (utcnow() - timedelta(hours=3)).replace(tzinfo=None)
    _touch_last_active(naive)
    assert utcnow() - naive.last_active < timedelta(seconds=5)
