import asyncio
import logging

from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from jose import JWTError

from trinetra_core.bus import SUBJECT_ALERTS, connect
from .auth import decode_token

log = logging.getLogger("trinetra.ws")
router = APIRouter()

clients: set[WebSocket] = set()


async def alert_broadcaster() -> None:
    while True:
        try:
            nc, _ = await connect()
            sub = await nc.subscribe(SUBJECT_ALERTS)
            log.info("alert broadcaster subscribed to %s", SUBJECT_ALERTS)
            async for msg in sub.messages:
                data = msg.data.decode()
                dead = []
                for ws in clients:
                    try:
                        await ws.send_text(data)
                    except Exception:
                        dead.append(ws)
                for ws in dead:
                    clients.discard(ws)
        except Exception as e:
            log.warning("broadcaster error: %s, reconnecting...", e)
            await asyncio.sleep(3)


@router.websocket("/ws/alerts")
async def ws_alerts(websocket: WebSocket, token: str = ""):
    try:
        if not token:
            await websocket.close(code=4401)
            return
        decode_token(token)
    except JWTError:
        await websocket.close(code=4401)
        return
    await websocket.accept()
    clients.add(websocket)
    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        clients.discard(websocket)
    except Exception:
        clients.discard(websocket)
