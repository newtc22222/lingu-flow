---
name: fastapi-guide
description: Conventions, layered architecture, and async SQLAlchemy patterns for FastAPI backend in LinguFlow.
---

# FastAPI & Backend Skill Guide

This skill provides guidelines and patterns for developing Python/FastAPI endpoints in the `backend/` directory.

## Layered Architecture

Always structure backend features using the following package structure:

```
backend/app/
├── routers/     # API endpoints, FastAPI APIRouter, HTTP handling
├── services/    # Business logic & DB interaction
├── models/      # SQLAlchemy ORM models (inheriting from Base)
├── schemas/     # Pydantic models (Input/Output data validation)
├── core/        # Security, dependencies, utilities
├── database.py  # Async DB session factory & Base class
├── config.py    # Environment settings
└── main.py      # App factory & router inclusion
```

## Core Conventions

1. **Async DB Operations**
   - Use `AsyncSession` injected via `db: AsyncSession = Depends(get_db)`.
   - Always await DB operations (`await db.execute(...)`, `await db.commit()`, etc.).

2. **Schema & API Contracts**
   - Use Pydantic v2 schemas (`BaseModel` with `ConfigDict(from_attributes=True)`).
   - Ensure router responses match what the Vue frontend expects. The frontend was **not** touched by the Node→FastAPI rewrite, so every call site (mostly under `frontend/src/features/**`, plus legacy `frontend/src/components/*.vue` and `frontend/src/utils/api.ts`) is the de facto spec — grep for the route path and read the exact fields it sends/reads before writing the schema, don't assume.
   - Decide the `_id` vs `id` question per endpoint: many frontend call sites still read Mongo-style `_id`. Default to Postgres-native `id` in the model/schema, and either update the frontend call site or alias in the Pydantic response schema (`serialization_alias="_id"`) — don't silently leave a mismatch.

3. **Router Registration**
   - Register all new routers in `backend/app/main.py` using `app.include_router(router, prefix="/api/...", tags=[...])`. Easy to forget — verify it manually after implementing.

4. **Known-stale docs — don't trust without cross-checking code**
   - `DEPLOYMENT.md` / `api/index.ts` describe deploying `backend/src` (Express) on Vercel; `backend/src` no longer exists (it's `backend/app`, FastAPI).
   - Root `.env.example` still lists `MONGO_URI`; real backend vars are in `backend/.env.example`.
   - No test suite exists yet (no pytest configured) — verify changes manually (start the app, exercise the frontend flow) rather than assuming a test will catch mistakes.

## Example Feature Template

### 1. Schema (`app/schemas/deck.py`)
```python
from pydantic import BaseModel, ConfigDict
from typing import Optional

class DeckBase(BaseModel):
    title: str
    description: Optional[str] = None

class DeckCreate(DeckBase):
    pass

class DeckResponse(DeckBase):
    id: int
    
    model_config = ConfigDict(from_attributes=True)
```

### 2. Model (`app/models/deck.py`)
```python
from sqlalchemy import Column, Integer, String, Text
from app.database import Base

class Deck(Base):
    __tablename__ = "decks"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
```

### 3. Service (`app/services/deck_service.py`)
```python
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from app.models.deck import Deck
from app.schemas.deck import DeckCreate

async def get_decks(db: AsyncSession):
    result = await db.execute(select(Deck))
    return result.scalars().all()

async def create_deck(db: AsyncSession, deck_in: DeckCreate):
    db_deck = Deck(**deck_in.model_dump())
    db.add(db_deck)
    await db.commit()
    await db.refresh(db_deck)
    return db_deck
```

### 4. Router (`app/routers/deck.py`)
```python
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List

from app.database import get_db
from app.schemas.deck import DeckCreate, DeckResponse
from app.services import deck_service

router = APIRouter()

@router.get("/", response_model=List[DeckResponse])
async def list_decks(db: AsyncSession = Depends(get_db)):
    return await deck_service.get_decks(db)

@router.post("/", response_model=DeckResponse, status_code=status.HTTP_201_CREATED)
async def create_deck(deck_in: DeckCreate, db: AsyncSession = Depends(get_db)):
    return await deck_service.create_deck(db, deck_in)
```
