"""Cross-platform configuration for Proto — The Proactive Agent.

All paths are derived from AGENT_HOME, which defaults to the directory
containing this file. Override any value via environment variables or a .env
file at the project root.
"""
from __future__ import annotations

import os
from pathlib import Path

try:
    from dotenv import load_dotenv  # type: ignore
    load_dotenv()
except Exception:  # pragma: no cover - optional dep
    pass


def _env(name: str, default: str) -> str:
    v = os.getenv(name)
    return v if v is not None and v != "" else default


def _env_int(name: str, default: int) -> int:
    try:
        return int(_env(name, str(default)))
    except ValueError:
        return default


def _env_float(name: str, default: float) -> float:
    try:
        return float(_env(name, str(default)))
    except ValueError:
        return default


# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------
AGENT_HOME: Path = Path(_env("AGENT_HOME", str(Path(__file__).resolve().parent)))
AGENT_HOME.mkdir(parents=True, exist_ok=True)

MEMORY_DIR: Path = AGENT_HOME / "memory"
STATE_DIR: Path = AGENT_HOME / "state"
LOGS_DIR: Path = AGENT_HOME / "logs"
for _p in (MEMORY_DIR, STATE_DIR, LOGS_DIR):
    _p.mkdir(parents=True, exist_ok=True)

EPISODIC_DB_PATH: Path = Path(_env("EPISODIC_DB_PATH", str(MEMORY_DIR / "episodic.db")))
SEMANTIC_DB_PATH: Path = Path(_env("SEMANTIC_DB_PATH", str(MEMORY_DIR / "semantic")))
TASKS_DB_PATH: Path = Path(_env("TASKS_DB_PATH", str(STATE_DIR / "tasks.db")))
CHECKPOINT_PATH: Path = Path(_env("CHECKPOINT_PATH", str(STATE_DIR / "checkpoint.json")))
HEARTBEAT_PATH: Path = Path(_env("HEARTBEAT_PATH", str(STATE_DIR / "heartbeat.txt")))
PID_PATH: Path = Path(_env("PID_PATH", str(STATE_DIR / "agent.pid")))
PAUSE_FLAG_PATH: Path = Path(_env("PAUSE_FLAG_PATH", str(STATE_DIR / "paused.flag")))

# ---------------------------------------------------------------------------
# LLM provider configuration
# ---------------------------------------------------------------------------
# LLM_PROVIDER: "ollama" (self-hosted, default) or "openai" (any OpenAI-compatible
# endpoint such as OpenAI, Together, Groq, OpenRouter, vLLM, llama.cpp server).
LLM_PROVIDER: str = _env("LLM_PROVIDER", "ollama").lower()

# Ollama (self-hosted)
OLLAMA_MODEL: str = _env("OLLAMA_MODEL", "qwen2.5:14b")
OLLAMA_BASE_URL: str = _env("OLLAMA_BASE_URL", "http://localhost:11434")
OLLAMA_TIMEOUT: int = _env_int("OLLAMA_TIMEOUT", 120)

# OpenAI-compatible (cloud or remote)
OPENAI_MODEL: str = _env("OPENAI_MODEL", "gpt-4o-mini")
OPENAI_BASE_URL: str = _env("OPENAI_BASE_URL", "https://api.openai.com/v1")
OPENAI_API_KEY: str = _env("OPENAI_API_KEY", "")
OPENAI_TIMEOUT: int = _env_int("OPENAI_TIMEOUT", 120)

# Active model name (whichever provider is selected)
LLM_MODEL: str = _env("LLM_MODEL", OPENAI_MODEL if LLM_PROVIDER == "openai" else OLLAMA_MODEL)

# ---------------------------------------------------------------------------
# Context / memory
# ---------------------------------------------------------------------------
MAX_CONTEXT_TOKENS: int = _env_int("MAX_CONTEXT_TOKENS", 4096)
CONTEXT_COMPRESSION_THRESHOLD: float = _env_float("CONTEXT_COMPRESSION_THRESHOLD", 0.75)
EPISODIC_RETENTION_DAYS: int = _env_int("EPISODIC_RETENTION_DAYS", 90)
MAX_RECALL_RESULTS: int = _env_int("MAX_RECALL_RESULTS", 8)

# ---------------------------------------------------------------------------
# Loop / scheduling
# ---------------------------------------------------------------------------
CHECKPOINT_INTERVAL_SECONDS: int = _env_int("CHECKPOINT_INTERVAL_SECONDS", 300)
REPLAN_INTERVAL_SECONDS: int = _env_int("REPLAN_INTERVAL_SECONDS", 86400)
HEARTBEAT_STALE_SECONDS: int = _env_int("HEARTBEAT_STALE_SECONDS", 120)
TOOL_MAX_RETRIES: int = _env_int("TOOL_MAX_RETRIES", 3)
TOOL_DEFAULT_TIMEOUT: int = _env_int("TOOL_DEFAULT_TIMEOUT", 60)
WATCHDOG_INTERVAL_SECONDS: int = _env_int("WATCHDOG_INTERVAL_SECONDS", 30)
MAX_MEMORY_MB: int = _env_int("MAX_MEMORY_MB", 4096)

# ---------------------------------------------------------------------------
# REST API
# ---------------------------------------------------------------------------
API_HOST: str = _env("API_HOST", "0.0.0.0")
API_PORT: int = _env_int("API_PORT", 8000)

# ---------------------------------------------------------------------------
# Misc
# ---------------------------------------------------------------------------
DEFAULT_GOAL: str = _env(
    "DEFAULT_GOAL",
    "Maintain and improve yourself. Learn about your environment and capabilities.",
)
