"""/logs router."""
from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path

from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import FileResponse

import config

router = APIRouter(prefix="/logs", tags=["logs"])


@router.get("/files")
def files() -> list[dict]:
    out = []
    for p in sorted(config.LOGS_DIR.glob("*.log"), key=lambda x: x.stat().st_mtime, reverse=True):
        st = p.stat()
        out.append(
            {
                "name": p.name,
                "size": st.st_size,
                "modified": datetime.fromtimestamp(st.st_mtime, tz=timezone.utc).isoformat(),
            }
        )
    return out


def _resolve(filename: str) -> Path:
    if filename in ("", "most recent"):
        files_list = sorted(config.LOGS_DIR.glob("*.log"), key=lambda x: x.stat().st_mtime, reverse=True)
        if not files_list:
            raise HTTPException(404, "no log files")
        return files_list[0]
    p = (config.LOGS_DIR / filename).resolve()
    if not str(p).startswith(str(config.LOGS_DIR.resolve())):
        raise HTTPException(400, "invalid path")
    if not p.exists():
        raise HTTPException(404, "log not found")
    return p


@router.get("/tail")
def tail(filename: str = Query("most recent"), lines: int = Query(200, ge=1, le=10000)) -> dict:
    p = _resolve(filename)
    with p.open("r", encoding="utf-8", errors="replace") as f:
        all_lines = f.readlines()
    return {"file": p.name, "lines": [ln.rstrip("\n") for ln in all_lines[-lines:]]}


@router.get("/download/{filename}")
def download(filename: str):
    p = _resolve(filename)
    return FileResponse(str(p), filename=p.name, media_type="text/plain")
