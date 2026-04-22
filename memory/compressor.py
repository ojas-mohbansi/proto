"""Context compressor: summarize text when it exceeds token budget."""
from __future__ import annotations


class ContextCompressor:
    @staticmethod
    def _approx_tokens(text: str) -> int:
        return max(1, len(text) // 4)

    def compress(self, text: str, max_tokens: int, llm_client) -> str:
        if self._approx_tokens(text) <= max_tokens:
            return text
        try:
            return llm_client.summarize(text, goal="preserve all decision-relevant facts")
        except Exception:
            # Hard truncate as last resort
            return text[: max_tokens * 4]
