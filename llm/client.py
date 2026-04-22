"""LLM client abstraction supporting Ollama (self-hosted) and OpenAI-compatible
endpoints (cloud or remote)."""
from __future__ import annotations

import json
from typing import Any

import httpx
from loguru import logger
from tenacity import retry, stop_after_attempt, wait_exponential

import config
from llm.prompts import ACTION_DECISION_PROMPT, SUMMARIZE_PROMPT


_FALLBACK_TEXT = "[LLM unavailable - using fallback]"


class _BaseClient:
    model: str
    base_url: str

    def complete(self, prompt: str, system: str | None = None) -> str:  # pragma: no cover
        raise NotImplementedError

    def is_available(self) -> bool:  # pragma: no cover
        raise NotImplementedError

    # -- shared helpers --------------------------------------------------
    def decide_action(self, context: str) -> dict[str, Any]:
        try:
            raw = self.complete(context, system=ACTION_DECISION_PROMPT)
            return _parse_json_object(raw)
        except Exception as e:
            logger.warning(f"decide_action first parse failed: {e}; retrying")
            try:
                raw = self.complete(
                    context + "\n\nReminder: respond with ONLY a valid JSON object.",
                    system=ACTION_DECISION_PROMPT,
                )
                return _parse_json_object(raw)
            except Exception as e2:
                logger.error(f"decide_action retry failed: {e2}")
                return {
                    "tool": "wait",
                    "args": {"seconds": 30},
                    "reasoning": "LLM decision unavailable",
                    "confidence": 0.0,
                    "reversible": True,
                }

    def summarize(self, text: str, goal: str) -> str:
        prompt = SUMMARIZE_PROMPT.format(goal=goal) + "\n\n---\n" + text
        return self.complete(prompt)


class OllamaClient(_BaseClient):
    def __init__(self, model: str | None = None, base_url: str | None = None) -> None:
        self.model = model or config.OLLAMA_MODEL
        self.base_url = (base_url or config.OLLAMA_BASE_URL).rstrip("/")
        self.client = httpx.Client(timeout=config.OLLAMA_TIMEOUT)

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(min=1, max=10))
    def _post_generate(self, payload: dict[str, Any]) -> dict[str, Any]:
        r = self.client.post(f"{self.base_url}/api/generate", json=payload)
        r.raise_for_status()
        return r.json()

    def complete(self, prompt: str, system: str | None = None) -> str:
        payload: dict[str, Any] = {
            "model": self.model,
            "prompt": prompt,
            "stream": False,
        }
        if system:
            payload["system"] = system
        try:
            data = self._post_generate(payload)
            return data.get("response", "")
        except Exception as e:
            logger.error(f"Ollama complete failed: {e}")
            return _FALLBACK_TEXT

    def is_available(self) -> bool:
        try:
            r = self.client.get(f"{self.base_url}/api/tags", timeout=5)
            return r.status_code == 200
        except Exception:
            return False


class OpenAIClient(_BaseClient):
    """OpenAI-compatible chat completions client. Works with OpenAI, Together,
    Groq, OpenRouter, vLLM, llama.cpp server, etc."""

    def __init__(
        self,
        model: str | None = None,
        base_url: str | None = None,
        api_key: str | None = None,
    ) -> None:
        self.model = model or config.OPENAI_MODEL
        self.base_url = (base_url or config.OPENAI_BASE_URL).rstrip("/")
        self.api_key = api_key if api_key is not None else config.OPENAI_API_KEY
        self.client = httpx.Client(timeout=config.OPENAI_TIMEOUT)

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(min=1, max=10))
    def _post_chat(self, payload: dict[str, Any]) -> dict[str, Any]:
        headers = {"Content-Type": "application/json"}
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"
        r = self.client.post(f"{self.base_url}/chat/completions", json=payload, headers=headers)
        r.raise_for_status()
        return r.json()

    def complete(self, prompt: str, system: str | None = None) -> str:
        messages = []
        if system:
            messages.append({"role": "system", "content": system})
        messages.append({"role": "user", "content": prompt})
        payload = {"model": self.model, "messages": messages, "stream": False}
        try:
            data = self._post_chat(payload)
            return data["choices"][0]["message"]["content"]
        except Exception as e:
            logger.error(f"OpenAI complete failed: {e}")
            return _FALLBACK_TEXT

    def is_available(self) -> bool:
        try:
            headers = {}
            if self.api_key:
                headers["Authorization"] = f"Bearer {self.api_key}"
            r = self.client.get(f"{self.base_url}/models", headers=headers, timeout=5)
            return r.status_code < 500
        except Exception:
            return False


def get_llm_client() -> _BaseClient:
    """Factory returning the configured LLM client."""
    provider = config.LLM_PROVIDER
    if provider == "openai":
        logger.info(f"LLM provider: openai ({config.OPENAI_MODEL} @ {config.OPENAI_BASE_URL})")
        return OpenAIClient()
    logger.info(f"LLM provider: ollama ({config.OLLAMA_MODEL} @ {config.OLLAMA_BASE_URL})")
    return OllamaClient()


# ---------------------------------------------------------------------------
def _parse_json_object(text: str) -> dict[str, Any]:
    """Extract the first JSON object from a model response."""
    text = text.strip()
    # Strip markdown code fences if present
    if text.startswith("```"):
        text = text.strip("`")
        if text.startswith("json"):
            text = text[4:]
    # Find first '{' and matching last '}'
    start = text.find("{")
    end = text.rfind("}")
    if start == -1 or end == -1 or end <= start:
        raise ValueError("no JSON object found")
    return json.loads(text[start : end + 1])
