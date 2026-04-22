"""/tasks router."""
from __future__ import annotations

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from planner.htn import HierarchicalPlanner

router = APIRouter(prefix="/tasks", tags=["tasks"])
_planner = HierarchicalPlanner()


@router.get("/")
def list_tasks() -> list[dict]:
    return [t.to_dict() for t in _planner.get_all_tasks()]


@router.get("/stats")
def stats() -> dict:
    return _planner.get_stats()


@router.get("/tree")
def tree() -> dict:
    return {"tree": _planner.get_tree_summary()}


@router.get("/{task_id}")
def get_task(task_id: str) -> dict:
    t = _planner.get_task_by_id(task_id)
    if not t:
        raise HTTPException(404, "task not found")
    return t.to_dict()


class AddTaskBody(BaseModel):
    goal: str
    parent_id: str | None = None
    completion_condition: str = ""


@router.post("/")
def add_task(body: AddTaskBody) -> dict:
    return _planner.add_task(body.goal, body.parent_id, body.completion_condition).to_dict()


class GoalBody(BaseModel):
    goal: str


@router.put("/{task_id}/goal")
def update_goal(task_id: str, body: GoalBody) -> dict:
    _planner.update_task_goal(task_id, body.goal)
    return {"ok": True}


class StatusBody(BaseModel):
    status: str
    reason: str = ""


@router.put("/{task_id}/status")
def update_status(task_id: str, body: StatusBody) -> dict:
    s = body.status.upper()
    if s == "DONE":
        _planner.mark_done(task_id)
    elif s == "FAILED":
        _planner.mark_failed(task_id, body.reason)
    else:
        _planner.update_task_status(task_id, s, body.reason)
    return {"ok": True}


@router.delete("/{task_id}")
def delete_task(task_id: str) -> dict:
    _planner.delete_task(task_id)
    return {"ok": True}
