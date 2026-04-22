"""Tool registry: safe wrappers around all agent-callable actions."""
from __future__ import annotations

import functools
import time
from pathlib import Path
from typing import Any, Callable

import httpx
from loguru import logger

import config
from tools.sandbox import run_sandboxed


def safe_tool(max_retries: int = 1, timeout: int = 60) -> Callable:
    def decorator(fn: Callable) -> Callable:
        @functools.wraps(fn)
        def wrapper(self, *args, **kwargs):
            name = fn.__name__
            attempt = 0
            last_err = ""
            t0 = time.time()
            while attempt < max_retries:
                attempt += 1
                try:
                    logger.info(f"TOOL {name} attempt {attempt} args={kwargs or args}")
                    res = fn(self, *args, **kwargs)
                    dt = time.time() - t0
                    logger.success(f"TOOL {name} ok in {dt:.2f}s")
                    return {"success": True, "result": res}
                except Exception as e:
                    last_err = str(e)
                    logger.warning(f"TOOL {name} failed attempt {attempt}: {e}")
            return {"success": False, "error": last_err}

        wrapper.__safe_tool__ = True  # type: ignore[attr-defined]
        wrapper.__timeout__ = timeout  # type: ignore[attr-defined]
        return wrapper

    return decorator


class ToolRegistry:
    def __init__(self, memory_manager, planner) -> None:
        self.memory = memory_manager
        self.planner = planner

    @safe_tool(max_retries=config.TOOL_MAX_RETRIES, timeout=config.TOOL_DEFAULT_TIMEOUT)
    def run_shell(self, cmd: str, timeout: int | None = None) -> dict[str, Any]:
        return run_sandboxed(cmd, timeout=timeout or config.TOOL_DEFAULT_TIMEOUT)

    @safe_tool(max_retries=config.TOOL_MAX_RETRIES)
    def web_fetch(self, url: str) -> dict[str, Any]:
        with httpx.Client(timeout=30, follow_redirects=True) as c:
            r = c.get(url)
            r.raise_for_status()
            return {"status": r.status_code, "text": r.text[:20000]}

    @safe_tool(max_retries=1)
    def read_file(self, path: str) -> str:
        return Path(path).expanduser().read_text(encoding="utf-8", errors="replace")

    @safe_tool(max_retries=1)
    def write_file(self, path: str, content: str) -> str:
        p = Path(path).expanduser()
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(content, encoding="utf-8")
        return f"wrote {len(content)} bytes to {p}"

    @safe_tool(max_retries=1)
    def search_memory(self, query: str, limit: int = 8) -> list[str]:
        return self.memory.recall_relevant(query, n=limit)

    @safe_tool(max_retries=1)
    def wait(self, seconds: int = 5) -> str:
        time.sleep(min(int(seconds), 300))
        return f"waited {seconds}s"

    @safe_tool(max_retries=1)
    def mark_task_done(self, task_id: str) -> str:
        self.planner.mark_done(task_id)
        return f"task {task_id} marked done"

    @safe_tool(max_retries=1)
    def mark_task_failed(self, task_id: str, reason: str = "") -> str:
        self.planner.mark_failed(task_id, reason)
        return f"task {task_id} marked failed"

    @safe_tool(max_retries=1)
    def spawn_subtask(self, parent_id: str, goal: str, completion_condition: str = "") -> dict[str, Any]:
        t = self.planner.add_task(goal, parent_id=parent_id, completion_condition=completion_condition)
        return t.to_dict()

    # -- dispatch ------------------------------------------------------
    def execute(self, tool: str, args: dict[str, Any] | None = None) -> dict[str, Any]:
        args = args or {}
        method = getattr(self, tool, None)
        if not method or not getattr(method, "__safe_tool__", False):
            return {"success": False, "error": f"unknown tool: {tool}"}
        try:
            return method(**args)
        except TypeError as e:
            return {"success": False, "error": f"bad args: {e}"}
