import asyncio
from typing import AsyncGenerator, Optional
from fastapi import APIRouter, Depends, Query, Request
from sse_starlette.sse import EventSourceResponse
from app.core.security import get_user_id_from_token

router = APIRouter(prefix="/api/events", tags=["Events"])


async def event_generator(request: Request, user_id: Optional[str]) -> AsyncGenerator[dict, None]:
    """Generates Server-Sent Events (SSE) stream for progress notifications and heartbeats."""
    # Send initial connection confirmation
    yield {
        "event": "connected",
        "data": '{"status": "connected", "userId": "' + (user_id or "anonymous") + '"}',
    }

    try:
        while True:
            if await request.is_disconnected():
                break

            # Send heartbeat keepalive ping every 15 seconds
            await asyncio.sleep(15)
            yield {
                "event": "ping",
                "data": '{"type": "keepalive"}',
            }
    except asyncio.CancelledError:
        pass


@router.get("", response_class=EventSourceResponse)
async def sse_events(
    request: Request,
    token: Optional[str] = Query(default=None),
):
    """Server-Sent Events (SSE) stream endpoint for real-time progress events."""
    user_id = None
    if token:
        user_id = get_user_id_from_token(token)

    return EventSourceResponse(event_generator(request, user_id))
