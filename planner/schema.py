"""Task schema and status enum."""
from __future__ import annotations

from dataclasses import asdict, dataclass, field
from enum import Enum
from typing import Any


class TaskStatus(str, Enum):
    PENDING = "PENDING"
    ACTIVE = "ACTIVE"
    BLOCKED = "BLOCKED"
    DONE = "DONE"
    FAILED = "FAILED"


@dataclass
class Task:
    id: str
    goal: str
    parent_id: str | None = None
    subtasks: list[str] = field(default_factory=list)
    status: str = TaskStatus.PENDING.value
    created_at: str = ""
    deadline: str | None = None
    completion_condition: str = ""
    estimated_hours: float = 1.0
    attempts: int = 0
    last_error: str = ""
    context_summary: str = ""

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_row(cls, row: dict[str, Any]) -> "Task":
        subs = row.get("subtasks") or ""
        if isinstance(subs, str):
            subs_list = [s for s in subs.split(",") if s]
        else:
            subs_list = list(subs)
        return cls(
            id=row["id"],
            goal=row["goal"],
            parent_id=row.get("parent_id"),
            subtasks=subs_list,
            status=row.get("status", TaskStatus.PENDING.value),
            created_at=row.get("created_at", ""),
            deadline=row.get("deadline"),
            completion_condition=row.get("completion_condition", ""),
            estimated_hours=float(row.get("estimated_hours", 1.0) or 1.0),
            attempts=int(row.get("attempts", 0) or 0),
            last_error=row.get("last_error", "") or "",
            context_summary=row.get("context_summary", "") or "",
        )
