"""Hierarchical Task Network planner backed by SQLite."""
from __future__ import annotations

import json
import sqlite3
import uuid
from datetime import datetime, timedelta, timezone
from typing import Any

from loguru import logger

import config
from llm.prompts import DECOMPOSE_GOAL_PROMPT
from planner.schema import Task, TaskStatus


class HierarchicalPlanner:
    def __init__(self) -> None:
        config.TASKS_DB_PATH.parent.mkdir(parents=True, exist_ok=True)
        self.conn = sqlite3.connect(str(config.TASKS_DB_PATH), check_same_thread=False)
        self.conn.row_factory = sqlite3.Row
        self.conn.execute(
            """
            CREATE TABLE IF NOT EXISTS tasks (
              id TEXT PRIMARY KEY,
              goal TEXT NOT NULL,
              parent_id TEXT,
              subtasks TEXT DEFAULT '',
              status TEXT DEFAULT 'PENDING',
              created_at TEXT NOT NULL,
              deadline TEXT,
              completion_condition TEXT DEFAULT '',
              estimated_hours REAL DEFAULT 1.0,
              attempts INTEGER DEFAULT 0,
              last_error TEXT DEFAULT '',
              context_summary TEXT DEFAULT ''
            )
            """
        )
        self.conn.commit()

    # -- existence -----------------------------------------------------
    def has_tasks(self) -> bool:
        r = self.conn.execute("SELECT COUNT(*) AS c FROM tasks").fetchone()
        return (r["c"] or 0) > 0

    # -- decomposition -------------------------------------------------
    def decompose_goal(self, goal: str, llm_client) -> list[Task]:
        prompt = DECOMPOSE_GOAL_PROMPT.format(goal=goal)
        raw = llm_client.complete(prompt)
        tasks: list[Task] = []
        try:
            data = _parse_json(raw)
            for t in data.get("tasks", []):
                tasks.append(
                    Task(
                        id=str(t.get("id") or uuid.uuid4()),
                        goal=t.get("goal", ""),
                        parent_id=t.get("parent_id"),
                        subtasks=list(t.get("subtasks", []) or []),
                        completion_condition=t.get("completion_condition", ""),
                        estimated_hours=float(t.get("estimated_hours", 1.0) or 1.0),
                        created_at=datetime.now(timezone.utc).isoformat(),
                    )
                )
        except Exception as e:
            logger.error(f"decompose_goal parse failed: {e}")
            # fallback: single task with the raw goal
            tasks = [Task(id=str(uuid.uuid4()), goal=goal, created_at=datetime.now(timezone.utc).isoformat())]
        for t in tasks:
            self._insert(t)
        return tasks

    # -- queries -------------------------------------------------------
    def get_next_task(self) -> Task | None:
        # leaf = no row with parent_id == this task is PENDING/ACTIVE
        rows = self.conn.execute(
            "SELECT * FROM tasks WHERE status = 'PENDING' ORDER BY created_at ASC"
        ).fetchall()
        for r in rows:
            children_open = self.conn.execute(
                "SELECT COUNT(*) AS c FROM tasks WHERE parent_id = ? AND status IN ('PENDING','ACTIVE')",
                (r["id"],),
            ).fetchone()["c"]
            if children_open == 0:
                self.conn.execute("UPDATE tasks SET status='ACTIVE' WHERE id=?", (r["id"],))
                self.conn.commit()
                return Task.from_row(dict(r))
        return None

    def get_all_tasks(self) -> list[Task]:
        rows = self.conn.execute("SELECT * FROM tasks ORDER BY created_at ASC").fetchall()
        return [Task.from_row(dict(r)) for r in rows]

    def get_task_by_id(self, task_id: str) -> Task | None:
        r = self.conn.execute("SELECT * FROM tasks WHERE id=?", (task_id,)).fetchone()
        return Task.from_row(dict(r)) if r else None

    def get_active_tasks(self) -> list[Task]:
        rows = self.conn.execute("SELECT * FROM tasks WHERE status='ACTIVE'").fetchall()
        return [Task.from_row(dict(r)) for r in rows]

    def get_completed_tasks(self, last_n_days: int = 7) -> list[Task]:
        cutoff = (datetime.now(timezone.utc) - timedelta(days=last_n_days)).isoformat()
        rows = self.conn.execute(
            "SELECT * FROM tasks WHERE status='DONE' AND created_at >= ?", (cutoff,)
        ).fetchall()
        return [Task.from_row(dict(r)) for r in rows]

    # -- mutations -----------------------------------------------------
    def mark_done(self, task_id: str) -> None:
        self.conn.execute("UPDATE tasks SET status='DONE' WHERE id=?", (task_id,))
        self.conn.commit()
        # recurse to parent
        parent = self.conn.execute(
            "SELECT parent_id FROM tasks WHERE id=?", (task_id,)
        ).fetchone()
        if parent and parent["parent_id"]:
            siblings = self.conn.execute(
                "SELECT status FROM tasks WHERE parent_id=?", (parent["parent_id"],)
            ).fetchall()
            if all(s["status"] == "DONE" for s in siblings):
                self.mark_done(parent["parent_id"])

    def mark_failed(self, task_id: str, reason: str) -> None:
        cur = self.conn.execute("SELECT attempts, parent_id FROM tasks WHERE id=?", (task_id,)).fetchone()
        if not cur:
            return
        attempts = (cur["attempts"] or 0) + 1
        if attempts < 3:
            self.conn.execute(
                "UPDATE tasks SET attempts=?, last_error=?, status='PENDING' WHERE id=?",
                (attempts, reason, task_id),
            )
        else:
            self.conn.execute(
                "UPDATE tasks SET attempts=?, last_error=?, status='FAILED' WHERE id=?",
                (attempts, reason, task_id),
            )
            if cur["parent_id"]:
                self.mark_failed(cur["parent_id"], f"child {task_id} failed: {reason}")
        self.conn.commit()

    def update_task_goal(self, task_id: str, new_goal: str) -> None:
        self.conn.execute("UPDATE tasks SET goal=? WHERE id=?", (new_goal, task_id))
        self.conn.commit()

    def update_task_status(self, task_id: str, status: str, reason: str = "") -> None:
        self.conn.execute(
            "UPDATE tasks SET status=?, last_error=? WHERE id=?",
            (status, reason, task_id),
        )
        self.conn.commit()

    def delete_task(self, task_id: str) -> None:
        children = self.conn.execute("SELECT id FROM tasks WHERE parent_id=?", (task_id,)).fetchall()
        for c in children:
            self.delete_task(c["id"])
        self.conn.execute("DELETE FROM tasks WHERE id=?", (task_id,))
        self.conn.commit()

    def add_task(self, goal: str, parent_id: str | None = None, completion_condition: str = "") -> Task:
        t = Task(
            id=str(uuid.uuid4()),
            goal=goal,
            parent_id=parent_id,
            completion_condition=completion_condition,
            created_at=datetime.now(timezone.utc).isoformat(),
        )
        self._insert(t)
        return t

    def re_evaluate(self, llm_client) -> str:
        stats = self.get_stats()
        summary = (
            f"Task summary: total={stats['total']}, pending={stats['pending']}, "
            f"active={stats['active']}, done={stats['done']}, failed={stats['failed']}"
        )
        try:
            prompt = (
                "You are reviewing a long-running agent's task list.\n"
                f"{summary}\nSuggest reprioritizations as JSON: "
                '{"raise":[ids],"lower":[ids],"drop":[ids]}'
            )
            raw = llm_client.complete(prompt)
            data = _parse_json(raw)
            for tid in data.get("drop", []) or []:
                self.update_task_status(tid, TaskStatus.BLOCKED.value, "deprioritized")
            logger.info(f"re_evaluate applied: {data}")
        except Exception as e:
            logger.warning(f"re_evaluate skipped: {e}")
        return summary

    def get_stats(self) -> dict[str, int]:
        rows = self.conn.execute("SELECT status, COUNT(*) AS c FROM tasks GROUP BY status").fetchall()
        out = {"total": 0, "pending": 0, "active": 0, "done": 0, "failed": 0, "blocked": 0}
        for r in rows:
            out[r["status"].lower()] = r["c"]
            out["total"] += r["c"]
        return out

    def get_tree_summary(self) -> str:
        symbols = {"PENDING": "[ ]", "ACTIVE": "[*]", "DONE": "[x]", "FAILED": "[!]", "BLOCKED": "[-]"}
        rows = [dict(r) for r in self.conn.execute("SELECT * FROM tasks").fetchall()]
        by_id = {r["id"]: r for r in rows}
        children: dict[str | None, list[dict]] = {}
        for r in rows:
            children.setdefault(r["parent_id"], []).append(r)

        lines: list[str] = []

        def walk(node_id: str | None, depth: int) -> None:
            for c in children.get(node_id, []):
                lines.append(
                    f"{'  ' * depth}{symbols.get(c['status'], '[?]')} {c['id'][:8]}  {c['goal'][:80]}"
                )
                walk(c["id"], depth + 1)

        walk(None, 0)
        return "\n".join(lines) if lines else "(empty)"

    # -- internals -----------------------------------------------------
    def _insert(self, t: Task) -> None:
        self.conn.execute(
            """
            INSERT OR REPLACE INTO tasks
            (id, goal, parent_id, subtasks, status, created_at, deadline,
             completion_condition, estimated_hours, attempts, last_error, context_summary)
            VALUES (?,?,?,?,?,?,?,?,?,?,?,?)
            """,
            (
                t.id, t.goal, t.parent_id, ",".join(t.subtasks), t.status,
                t.created_at or datetime.now(timezone.utc).isoformat(),
                t.deadline, t.completion_condition, t.estimated_hours,
                t.attempts, t.last_error, t.context_summary,
            ),
        )
        self.conn.commit()


def _parse_json(text: str) -> dict[str, Any]:
    text = text.strip()
    if text.startswith("```"):
        text = text.strip("`")
        if text.startswith("json"):
            text = text[4:]
    s = text.find("{")
    e = text.rfind("}")
    if s == -1 or e == -1:
        raise ValueError("no JSON")
    return json.loads(text[s : e + 1])
