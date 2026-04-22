"""Autonomous agent main loop."""
from __future__ import annotations

import asyncio
import json
import os
import signal
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

from loguru import logger

import config
from llm.client import get_llm_client
from memory.compressor import ContextCompressor
from memory.manager import MemoryManager
from planner.htn import HierarchicalPlanner
from tools.registry import ToolRegistry


def _setup_logging() -> None:
    logger.remove()
    logger.add(sys.stderr, level="INFO")
    logger.add(
        str(config.LOGS_DIR / "agent_{time:YYYY-MM-DD}.log"),
        rotation="10 MB",
        retention="30 days",
        level="DEBUG",
    )


def load_checkpoint() -> dict:
    if config.CHECKPOINT_PATH.exists():
        try:
            return json.loads(config.CHECKPOINT_PATH.read_text())
        except Exception:
            return {}
    return {}


def save_checkpoint(data: dict) -> None:
    config.CHECKPOINT_PATH.parent.mkdir(parents=True, exist_ok=True)
    tmp = config.CHECKPOINT_PATH.with_suffix(".json.tmp")
    tmp.write_text(json.dumps(data, indent=2))
    os.replace(tmp, config.CHECKPOINT_PATH)


def write_heartbeat() -> None:
    config.HEARTBEAT_PATH.write_text(datetime.now(timezone.utc).isoformat())


def write_pid() -> None:
    config.PID_PATH.write_text(str(os.getpid()))


_stop = False


def setup_signal_handlers() -> None:
    def _handler(signum, frame):
        global _stop
        _stop = True
        logger.warning(f"received signal {signum}; will stop after current iteration")

    signal.signal(signal.SIGINT, _handler)
    signal.signal(signal.SIGTERM, _handler)


async def agent_loop(goal: str) -> None:
    write_pid()
    mem = MemoryManager()
    planner = HierarchicalPlanner()
    llm = get_llm_client()
    tools = ToolRegistry(mem, planner)
    compressor = ContextCompressor()

    ck = load_checkpoint()
    if not ck.get("goal"):
        ck["goal"] = goal
    ck.setdefault("iteration", 0)
    ck.setdefault("tasks_completed", 0)
    ck.setdefault("tasks_failed", 0)
    save_checkpoint(ck)

    if not planner.has_tasks():
        logger.info(f"decomposing goal: {ck['goal']}")
        planner.decompose_goal(ck["goal"], llm)

    last_checkpoint = time.time()
    last_replan = time.time()
    last_prune = time.time()

    while not _stop:
        try:
            write_heartbeat()
            ck["iteration"] = int(ck.get("iteration", 0)) + 1

            if config.PAUSE_FLAG_PATH.exists():
                logger.info("paused; sleeping 30s")
                await asyncio.sleep(30)
                continue

            task = planner.get_next_task()
            if task is None:
                logger.info("no pending tasks; sleeping")
                await asyncio.sleep(30)
                continue

            ck["current_task_id"] = task.id

            ctx = mem.build_context_window(
                {"id": task.id, "goal": task.goal, "plan_status": planner.get_stats(), "current_step": task.goal}
            )
            ctx = compressor.compress(ctx, config.MAX_CONTEXT_TOKENS, llm)

            decision = llm.decide_action(ctx)
            logger.info(f"decision: {decision.get('tool')} ({decision.get('confidence')})")

            ok, why = mem.verify_action(decision)
            if not ok:
                logger.warning(f"action rejected by memory check: {why}")
                mem.remember(task.id, json.dumps(decision), f"REJECTED: {why}", success=False)
                await asyncio.sleep(1)
                continue

            tool_name = decision.get("tool", "wait")
            args = decision.get("args", {}) or {}
            res = tools.execute(tool_name, args)
            success = bool(res.get("success"))
            payload = json.dumps(res)[:4000]
            mem.remember(task.id, json.dumps({"tool": tool_name, "args": args}), payload, success=success)

            if tool_name == "mark_task_done" and success:
                ck["tasks_completed"] = int(ck.get("tasks_completed", 0)) + 1
            if tool_name == "mark_task_failed" and success:
                ck["tasks_failed"] = int(ck.get("tasks_failed", 0)) + 1

            now = time.time()
            if now - last_checkpoint >= config.CHECKPOINT_INTERVAL_SECONDS:
                save_checkpoint(ck)
                last_checkpoint = now
            if now - last_replan >= config.REPLAN_INTERVAL_SECONDS:
                planner.re_evaluate(llm)
                last_replan = now
            if now - last_prune >= 86400:
                deleted = mem.prune_old_episodes()
                logger.info(f"pruned {deleted} old episodes")
                last_prune = now

        except Exception as e:
            logger.exception(f"loop error: {e}")
            await asyncio.sleep(5)

        await asyncio.sleep(1)

    save_checkpoint(ck)
    logger.info("agent loop exited")


def main() -> None:
    _setup_logging()
    setup_signal_handlers()
    goal = " ".join(sys.argv[1:]).strip() or config.DEFAULT_GOAL
    logger.info(f"starting agent with goal: {goal}")
    logger.info(f"AGENT_HOME={config.AGENT_HOME}")
    logger.info(f"LLM provider={config.LLM_PROVIDER} model={config.LLM_MODEL}")
    asyncio.run(agent_loop(goal))


if __name__ == "__main__":
    main()
