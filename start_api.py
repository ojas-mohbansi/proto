"""Run the FastAPI server."""
from __future__ import annotations

import os

import uvicorn

import config


def main() -> None:
    host = os.environ.get("API_HOST", config.API_HOST)
    port = int(os.environ.get("PORT") or os.environ.get("API_PORT") or config.API_PORT)
    print(f"Agent API starting on http://{host}:{port}")
    print(f"  Docs:  http://{host}:{port}/docs")
    print(f"  Logs WS: ws://{host}:{port}/ws/logs")
    print(f"  LLM provider: {config.LLM_PROVIDER}  model: {config.LLM_MODEL}")
    try:
        uvicorn.run("webui.app:app", host=host, port=port, log_level="info")
    except KeyboardInterrupt:
        print("\nShutting down API.")


if __name__ == "__main__":
    main()
