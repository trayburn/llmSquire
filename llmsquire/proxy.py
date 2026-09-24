"""Proxy module for the `llm` object that student koan files import.

The student writes `from llmsquire import Koan, llm` in their koan file.
At runtime, the Sensei runner sets `llm._client` to the current test's
`self.llm` instance (a fresh LLMClient per test). All calls to
`llm.ask()` and `llm.converse()` delegate to that per-test client.

Before the Sensei sets a client, calls raise a helpful error.
"""
from __future__ import annotations

from typing import Any, Dict, List, Optional

from llmsquire.llm_client import LLMClient


class _LLMProxy:
    """Delegates ask()/converse() to the current test's LLMClient instance."""

    def __init__(self):
        self._client: Optional[LLMClient] = None

    def _resolve(self):
        if self._client is None:
            raise RuntimeError(
                "llm is not available outside of a koan test.\n"
                "The Sensei runner sets llm._client before each test.\n"
                "Run with: python -m llmsquire"
            )
        return self._client

    @property
    def trace(self):
        return self._resolve().trace

    def ask(
        self,
        messages: List[Dict[str, Any]],
        tools: Optional[List[Dict]] = None,
        model: Optional[str] = None,
        temperature: float = 0.0,
    ):
        return self._resolve().ask(
            messages=messages, tools=tools, model=model, temperature=temperature
        )

    def converse(
        self,
        messages: List[Dict[str, Any]],
        tools: Optional[List[Dict]] = None,
        tool_implementations: Optional[Dict[str, Any]] = None,
        model: Optional[str] = None,
        temperature: float = 0.0,
        max_iterations: int = 10,
    ):
        return self._resolve().converse(
            messages=messages,
            tools=tools,
            tool_implementations=tool_implementations,
            model=model,
            temperature=temperature,
            max_iterations=max_iterations,
        )


# Singleton proxy — the Sensei runner sets _client before each test
llm = _LLMProxy()