"""Sandboxed shell execution with cross-platform blocklist."""
from __future__ import annotations

import re
import subprocess
import sys
from typing import Any

from loguru import logger

# Patterns blocked on any platform.
_BLOCKLIST = [
    r"\bdel\s+/f\s+/s",
    r"\bformat\s+[a-zA-Z]:",
    r"\bshutdown\b",
    r"\breg\s+delete\b",
    r"\brmdir\s+/s",
    r"\brd\s+/s",
    r"Remove-Item\s+-Recurse",
    r"\brm\s+-rf\s+/",
    r"\bmkfs\b",
    r":\(\)\s*\{",  # fork bomb
    r"\bdd\s+if=.*of=/dev/",
    r"\bchmod\s+-R\s+0\s+/",
]


def run_sandboxed(cmd: str, timeout: int = 60) -> dict[str, Any]:
    for pat in _BLOCKLIST:
        if re.search(pat, cmd, flags=re.IGNORECASE):
            logger.warning(f"BLOCKED command: {cmd}")
            return {
                "stdout": "",
                "stderr": f"blocked by sandbox policy: {pat}",
                "returncode": 1,
                "blocked": True,
            }
    try:
        # shell=True so users can pipe; sandbox policy is enforced via blocklist
        proc = subprocess.run(
            cmd,
            shell=True,
            capture_output=True,
            text=True,
            timeout=timeout,
        )
        return {
            "stdout": proc.stdout,
            "stderr": proc.stderr,
            "returncode": proc.returncode,
            "blocked": False,
        }
    except subprocess.TimeoutExpired as e:
        return {
            "stdout": e.stdout or "",
            "stderr": f"timeout after {timeout}s",
            "returncode": 124,
            "blocked": False,
        }
    except Exception as e:
        return {"stdout": "", "stderr": str(e), "returncode": 1, "blocked": False}


def platform_name() -> str:
    return "windows" if sys.platform.startswith("win") else "linux"
