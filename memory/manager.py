"""Episodic (SQLite) + semantic (ChromaDB) memory manager."""
from __future__ import annotations

import sqlite3
import uuid
from datetime import datetime, timedelta, timezone
from typing import Any

try:
    import chromadb  # type: ignore
except Exception:  # pragma: no cover - chromadb is optional in degraded mode
    chromadb = None  # type: ignore

from loguru import logger

import config


class _NullCollection:
    """No-op semantic store used when chromadb is unavailable."""

    def add(self, *_a, **_k): pass
    def query(self, *_a, **_k): return {"documents": [[]]}
    def count(self): return 0


class MemoryManager:
    def __init__(self) -> None:
        config.MEMORY_DIR.mkdir(parents=True, exist_ok=True)
        config.SEMANTIC_DB_PATH.mkdir(parents=True, exist_ok=True)

        if chromadb is not None:
            try:
                self.chroma = chromadb.PersistentClient(path=str(config.SEMANTIC_DB_PATH))
                self.collection = self.chroma.get_or_create_collection("agent_memory")
            except Exception as e:
                logger.warning(f"chromadb init failed, running without semantic memory: {e}")
                self.chroma = None
                self.collection = _NullCollection()
        else:
            logger.warning("chromadb not installed; semantic memory disabled.")
            self.chroma = None
            self.collection = _NullCollection()

        self.conn = sqlite3.connect(str(config.EPISODIC_DB_PATH), check_same_thread=False)
        self.conn.row_factory = sqlite3.Row
        self.conn.execute(
            """
            CREATE TABLE IF NOT EXISTS episodes (
              id TEXT PRIMARY KEY,
              timestamp TEXT NOT NULL,
              task_id TEXT,
              action TEXT,
              result TEXT,
              success INTEGER
            )
            """
        )
        self.conn.commit()

    # -- write ----------------------------------------------------------
    def remember(self, task_id: str, action: str, result: str, success: bool) -> str:
        eid = str(uuid.uuid4())
        ts = datetime.now(timezone.utc).isoformat()
        self.conn.execute(
            "INSERT INTO episodes (id, timestamp, task_id, action, result, success) VALUES (?,?,?,?,?,?)",
            (eid, ts, task_id, action, result, 1 if success else 0),
        )
        self.conn.commit()
        try:
            doc = f"ACTION: {action}\nRESULT: {result}\nSUCCESS: {success}"
            self.collection.add(
                ids=[eid],
                documents=[doc],
                metadatas=[{"task_id": task_id or "", "success": bool(success)}],
            )
        except Exception as e:
            logger.warning(f"chroma add failed: {e}")
        return eid

    # -- recall ---------------------------------------------------------
    def recall_relevant(self, query: str, n: int | None = None) -> list[str]:
        n = n or config.MAX_RECALL_RESULTS
        try:
            if self.collection.count() == 0:
                return []
            res = self.collection.query(query_texts=[query], n_results=min(n, self.collection.count()))
            docs = res.get("documents") or [[]]
            return list(docs[0]) if docs else []
        except Exception as e:
            logger.warning(f"recall_relevant failed: {e}")
            return []

    def get_recent_episodes(self, task_id: str, limit: int = 10) -> list[dict[str, Any]]:
        rows = self.conn.execute(
            "SELECT * FROM episodes WHERE task_id = ? ORDER BY timestamp DESC LIMIT ?",
            (task_id, limit),
        ).fetchall()
        return [_row_to_dict(r) for r in rows]

    def get_all_episodes(self, limit: int = 100, offset: int = 0) -> list[dict[str, Any]]:
        rows = self.conn.execute(
            "SELECT * FROM episodes ORDER BY timestamp DESC LIMIT ? OFFSET ?",
            (limit, offset),
        ).fetchall()
        return [_row_to_dict(r) for r in rows]

    def search_episodes(self, query: str, limit: int = 50) -> list[dict[str, Any]]:
        like = f"%{query}%"
        rows = self.conn.execute(
            "SELECT * FROM episodes WHERE action LIKE ? OR result LIKE ? ORDER BY timestamp DESC LIMIT ?",
            (like, like, limit),
        ).fetchall()
        results = {r["id"]: _row_to_dict(r) for r in rows}
        for doc in self.recall_relevant(query, n=limit):
            # try to find matching row by content
            for r in self.conn.execute(
                "SELECT * FROM episodes WHERE action LIKE ? OR result LIKE ? LIMIT 5",
                (f"%{doc[:60]}%", f"%{doc[:60]}%"),
            ).fetchall():
                results.setdefault(r["id"], _row_to_dict(r))
        return list(results.values())[:limit]

    # -- context --------------------------------------------------------
    def build_context_window(self, task: dict[str, Any]) -> str:
        relevant = self.recall_relevant(task.get("goal", ""))
        recent = self.get_recent_episodes(task.get("id", ""), limit=10)
        sections = [
            f"AGENT GOAL: {task.get('goal', '')}",
            f"PLAN STATUS: {task.get('plan_status', '')}",
            f"CURRENT STEP: {task.get('current_step', '')}",
            "",
            "RELEVANT KNOWLEDGE FROM MEMORY:",
        ]
        sections.extend(f"- {r}" for r in relevant) if relevant else sections.append("- (none)")
        sections.append("")
        sections.append("RECENT ACTIONS:")
        if recent:
            for ep in recent:
                ok = "OK" if ep["success"] else "FAILED"
                sections.append(f"[{ep['timestamp']}] {ok}: {ep['action']} -> {ep['result'][:200]}")
        else:
            sections.append("(none)")
        return "\n".join(sections)

    # -- maintenance ----------------------------------------------------
    def prune_old_episodes(self, days: int | None = None) -> int:
        days = days or config.EPISODIC_RETENTION_DAYS
        cutoff = (datetime.now(timezone.utc) - timedelta(days=days)).isoformat()
        cur = self.conn.execute("DELETE FROM episodes WHERE timestamp < ?", (cutoff,))
        self.conn.commit()
        return cur.rowcount

    def verify_action(self, action: dict[str, Any]) -> tuple[bool, str]:
        tool = action.get("tool", "")
        args = str(action.get("args", ""))
        results = self.recall_relevant(f"{tool} {args}")
        failed = [r for r in results if "FAILED" in r.upper()]
        if len(failed) > 2:
            return False, f"Similar action failed {len(failed)} times before"
        return True, ""

    def get_stats(self) -> dict[str, Any]:
        cur = self.conn.execute(
            "SELECT COUNT(*) AS total,"
            " SUM(CASE WHEN success=1 THEN 1 ELSE 0 END) AS ok,"
            " SUM(CASE WHEN success=0 THEN 1 ELSE 0 END) AS bad,"
            " COUNT(DISTINCT task_id) AS tasks,"
            " MIN(timestamp) AS oldest FROM episodes"
        ).fetchone()
        return {
            "total_episodes": cur["total"] or 0,
            "successful_episodes": cur["ok"] or 0,
            "failed_episodes": cur["bad"] or 0,
            "unique_tasks": cur["tasks"] or 0,
            "oldest_episode": cur["oldest"],
        }


def _row_to_dict(r: sqlite3.Row) -> dict[str, Any]:
    return {
        "id": r["id"],
        "timestamp": r["timestamp"],
        "task_id": r["task_id"],
        "action": r["action"],
        "result": r["result"],
        "success": bool(r["success"]),
    }
