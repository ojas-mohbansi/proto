"""/memory router."""
from __future__ import annotations

from fastapi import APIRouter, Query

from memory.manager import MemoryManager

router = APIRouter(prefix="/memory", tags=["memory"])
_mem = MemoryManager()


@router.get("/stats")
def stats() -> dict:
    return _mem.get_stats()


@router.get("/episodes")
def episodes(
    limit: int = Query(100, ge=1, le=500),
    offset: int = Query(0, ge=0),
    task_id: str | None = None,
) -> list[dict]:
    if task_id:
        return _mem.get_recent_episodes(task_id, limit=limit)
    return _mem.get_all_episodes(limit=limit, offset=offset)


@router.get("/search")
def search(q: str = Query(...), limit: int = Query(50, ge=1, le=200)) -> list[dict]:
    return _mem.search_episodes(q, limit=limit)


@router.delete("/prune")
def prune(days: int | None = None) -> dict:
    deleted = _mem.prune_old_episodes(days)
    return {"ok": True, "deleted": deleted}
