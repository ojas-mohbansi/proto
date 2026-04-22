"""/agent router."""
from __future__ import annotations

import json
import os
import tempfile
from datetime import datetime, timezone
from pathlib import Path

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

import config
from llm.client import get_llm_client
from watchdog.monitor import is_heartbeat_stale

router = APIRouter(prefix="/agent", tags=["agent"])


def _read_checkpoint() -> dict:
    if not config.CHECKPOINT_PATH.exists():
        return {}
    try:
        return json.loads(config.CHECKPOINT_PATH.read_text())
    except Exception:
        return {}


def _atomic_write_checkpoint(data: dict) -> None:
    config.CHECKPOINT_PATH.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp = tempfile.mkstemp(dir=str(config.CHECKPOINT_PATH.parent), prefix=".ck-", suffix=".json")
    os.close(fd)
    Path(tmp).write_text(json.dumps(data, indent=2))
    os.replace(tmp, config.CHECKPOINT_PATH)


@router.get("/status")
def status() -> dict:
    ck = _read_checkpoint()
    last_hb = None
    if config.HEARTBEAT_PATH.exists():
        last_hb = config.HEARTBEAT_PATH.read_text().strip()
    running = not is_heartbeat_stale()
    try:
        ollama_ok = get_llm_client().is_available()
    except Exception:
        ollama_ok = False
    return {
        "status": "running" if running else "stopped",
        "last_heartbeat": last_hb,
        "goal": ck.get("goal"),
        "current_task_id": ck.get("current_task_id"),
        "iteration": ck.get("iteration", 0),
        "tasks_completed": ck.get("tasks_completed", 0),
        "tasks_failed": ck.get("tasks_failed", 0),
        "ollama_available": ollama_ok,
        "paused": config.PAUSE_FLAG_PATH.exists(),
        "llm_provider": config.LLM_PROVIDER,
        "llm_model": config.LLM_MODEL,
    }


@router.get("/checkpoint")
def checkpoint() -> dict:
    if not config.CHECKPOINT_PATH.exists():
        raise HTTPException(404, "checkpoint not found")
    return _read_checkpoint() | {
        "model": config.LLM_MODEL,
        "api_url": f"http://{config.API_HOST}:{config.API_PORT}",
        "checkpoint_interval": config.CHECKPOINT_INTERVAL_SECONDS,
        "replan_interval": config.REPLAN_INTERVAL_SECONDS,
        "llm_provider": config.LLM_PROVIDER,
    }


class GoalBody(BaseModel):
    goal: str


@router.post("/goal")
def set_goal(body: GoalBody) -> dict:
    if not is_heartbeat_stale():
        raise HTTPException(
            status_code=409,
            detail="agent is currently running; pause or stop it before injecting a new goal",
        )
    ck = _read_checkpoint()
    ck["goal"] = body.goal
    ck["goal_set_at"] = datetime.now(timezone.utc).isoformat()
    _atomic_write_checkpoint(ck)
    try:
        if config.TASKS_DB_PATH.exists():
            config.TASKS_DB_PATH.unlink()
    except Exception:
        pass
    return {"ok": True, "goal": body.goal}


@router.post("/pause")
def pause() -> dict:
    config.PAUSE_FLAG_PATH.parent.mkdir(parents=True, exist_ok=True)
    config.PAUSE_FLAG_PATH.touch()
    return {"ok": True, "paused": True}


@router.post("/resume")
def resume() -> dict:
    if config.PAUSE_FLAG_PATH.exists():
        config.PAUSE_FLAG_PATH.unlink()
    return {"ok": True, "paused": False}


@router.get("/pid")
def pid() -> dict:
    if not config.PID_PATH.exists():
        return {"pid": None}
    try:
        return {"pid": int(config.PID_PATH.read_text().strip())}
    except Exception:
        return {"pid": None}
