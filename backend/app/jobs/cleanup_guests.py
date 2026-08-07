"""Delete guest accounts that have been idle past the retention window.

Run as a one-shot command (Railway cron service, or by hand):

    python -m app.jobs.cleanup_guests

Exits non-zero on failure so a scheduler can surface the run as failed.
"""

import asyncio
import logging
import sys

from app.database import AsyncSessionLocal, engine
from app.services.guest_service import cleanup_inactive_guests

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("linguflow")


async def main() -> int:
    try:
        async with AsyncSessionLocal() as session:
            await cleanup_inactive_guests(session)
    except Exception:
        logger.exception("Guest cleanup failed")
        return 1
    finally:
        await engine.dispose()
    return 0


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
