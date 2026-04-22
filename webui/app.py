"""FastAPI app exposing the agent's REST API + WebSocket log stream."""
from __future__ import annotations

import asyncio
import os
from pathlib import Path

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware

import config
from webui.routers import agent as agent_router
from webui.routers import logs as logs_router
from webui.routers import memory as memory_router
from webui.routers import tasks as tasks_router

URL_PREFIX = os.environ.get("URL_PREFIX", "").rstrip("/")

app = FastAPI(title="Proto — The Proactive Agent API", version="1.0.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)
app.include_router(agent_router.router, prefix=URL_PREFIX)
app.include_router(tasks_router.router, prefix=URL_PREFIX)
app.include_router(memory_router.router, prefix=URL_PREFIX)
app.include_router(logs_router.router, prefix=URL_PREFIX)


@app.get("/")
def root() -> dict:
    return {"name": "Proto — The Proactive Agent API", "version": "1.0.0", "docs": "/docs", "prefix": URL_PREFIX}


@app.get(f"{URL_PREFIX}/healthz")
def healthz() -> dict:
    return {"ok": True}


def _latest_log_file() -> Path | None:
    files = sorted(config.LOGS_DIR.glob("*.log"), key=lambda p: p.stat().st_mtime, reverse=True)
    return files[0] if files else None


@app.websocket(f"{URL_PREFIX}/ws/logs")
async def ws_logs(ws: WebSocket) -> None:
    await ws.accept()
    log_path = _latest_log_file()
    if log_path is None:
        await ws.send_text("[no log files yet]")
        try:
            while True:
                await asyncio.sleep(2)
                log_path = _latest_log_file()
                if log_path:
                    await ws.send_text(f"[tailing {log_path.name}]")
                    break
        except WebSocketDisconnect:
            return
    pos = log_path.stat().st_size
    try:
        while True:
            try:
                size = log_path.stat().st_size
                if size < pos:
                    pos = 0  # rotated
                if size > pos:
                    with log_path.open("r", encoding="utf-8", errors="replace") as f:
                        f.seek(pos)
                        chunk = f.read()
                        pos = f.tell()
                    for line in chunk.splitlines():
                        await ws.send_text(line)
            except FileNotFoundError:
                pass
            await asyncio.sleep(0.5)
    except WebSocketDisconnect:
        return
    except Exception:
        return
