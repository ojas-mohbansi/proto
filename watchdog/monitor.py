"""Watchdog: monitors the agent process and restarts on crash/stale heartbeat."""
from __future__ import annotations

import os
import signal
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

import psutil
from loguru import logger

import config


def is_paused() -> bool:
    return config.PAUSE_FLAG_PATH.exists()


def is_heartbeat_stale() -> bool:
    if not config.HEARTBEAT_PATH.exists():
        return True
    try:
        ts = config.HEARTBEAT_PATH.read_text().strip()
        last = datetime.fromisoformat(ts)
        if last.tzinfo is None:
            last = last.replace(tzinfo=timezone.utc)
        delta = (datetime.now(timezone.utc) - last).total_seconds()
        return delta > config.HEARTBEAT_STALE_SECONDS
    except Exception:
        return True


def _read_pid() -> int | None:
    try:
        return int(config.PID_PATH.read_text().strip())
    except Exception:
        return None


def is_memory_exceeded() -> bool:
    pid = _read_pid()
    if not pid:
        return False
    try:
        p = psutil.Process(pid)
        rss_mb = p.memory_info().rss / (1024 * 1024)
        return rss_mb > config.MAX_MEMORY_MB
    except Exception:
        return False


def kill_agent() -> None:
    pid = _read_pid()
    if not pid:
        return
    try:
        p = psutil.Process(pid)
        p.terminate()
        try:
            p.wait(timeout=10)
        except psutil.TimeoutExpired:
            p.kill()
        logger.warning(f"watchdog killed agent pid={pid}")
    except Exception as e:
        logger.warning(f"kill_agent: {e}")


def start_agent() -> None:
    main_py = Path(__file__).resolve().parent.parent / "main.py"
    logger.info(f"watchdog starting agent: {sys.executable} {main_py}")
    creationflags = 0
    if sys.platform.startswith("win"):
        creationflags = getattr(subprocess, "CREATE_NEW_PROCESS_GROUP", 0)
    subprocess.Popen([sys.executable, str(main_py)], creationflags=creationflags)


def run_watchdog() -> None:
    logger.add(str(config.LOGS_DIR / "watchdog.log"), rotation="10 MB", retention="30 days")
    logger.info("watchdog started")
    while True:
        try:
            if is_paused():
                logger.info("watchdog: agent intentionally paused, skipping restart")
            elif is_heartbeat_stale() or is_memory_exceeded():
                logger.warning("watchdog: heartbeat stale or memory exceeded; restarting agent")
                kill_agent()
                time.sleep(2)
                start_agent()
        except Exception as e:
            logger.error(f"watchdog loop error: {e}")
        time.sleep(config.WATCHDOG_INTERVAL_SECONDS)


if __name__ == "__main__":
    run_watchdog()
