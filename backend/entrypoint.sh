#!/bin/sh
set -e

# One process owns migrate + seed before any uvicorn workers start. Seeding
# used to live in FastAPI lifespan, which raced when --workers > 1.
alembic upgrade head
python -m app.seed.exam_seed
exec uvicorn app.main:app --host 0.0.0.0 --port "${PORT:-8000}"
