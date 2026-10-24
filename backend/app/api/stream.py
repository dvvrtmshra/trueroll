"""SSE stream endpoint — live events for the officer dashboard."""
import asyncio
import json

from fastapi import APIRouter, Query
from fastapi.responses import StreamingResponse

from app.core import events as event_bus
from app.core.security import decode_token

router = APIRouter()


@router.get("")
async def stream(token: str = Query(...)):
    """Server-Sent Events stream. Token passed as query param (EventSource limitation)."""
    try:
        decode_token(token)
    except Exception:
        async def _denied():
            yield "data: {\"error\": \"unauthorized\"}\n\n"
        return StreamingResponse(_denied(), media_type="text/event-stream")

    q = event_bus.subscribe()

    async def _generate():
        try:
            heartbeat = 0
            while True:
                try:
                    event = await asyncio.wait_for(q.get(), timeout=15.0)
                    yield f"data: {json.dumps(event)}\n\n"
                except asyncio.TimeoutError:
                    heartbeat += 1
                    yield f": heartbeat {heartbeat}\n\n"
        finally:
            event_bus.unsubscribe(q)

    return StreamingResponse(
        _generate(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",
        },
    )
