from __future__ import annotations

from typing import Any, Dict, Iterator, List, Optional

import dashscope
from dashscope import Generation


class Qwen3Client:
    def __init__(self, api_key: Optional[str], model: str) -> None:
        # Keep a default key for environments that prefer env-based auth.
        # We will still allow per-request override via Generation.call(api_key=...).
        if api_key:
            dashscope.api_key = api_key
        self.model = model

    def complete(
        self,
        messages: List[Dict[str, Any]],
        *,
        api_key: Optional[str] = None,
        temperature: float = 0.2,
    ) -> str:
        resp = Generation.call(
            api_key=api_key,
            model=self.model,
            messages=messages,
            temperature=temperature,
            result_format="message",
        )
        if resp.status_code != 200:
            raise RuntimeError(f"DashScope error: {resp.status_code} {getattr(resp,'code',None)} {getattr(resp,'message',None)}")
        return resp.output.choices[0].message.content

    def stream(
        self,
        messages: List[Dict[str, Any]],
        *,
        api_key: Optional[str] = None,
        temperature: float = 0.2,
    ) -> Iterator[str]:
        # DashScope SDK returns a generator of response chunks when stream=True.
        responses = Generation.call(
            api_key=api_key,
            model=self.model,
            messages=messages,
            temperature=temperature,
            result_format="message",
            stream=True,
            incremental_output=True,
        )
        for r in responses:
            if getattr(r, "status_code", 500) != 200:
                raise RuntimeError(f"DashScope stream error: {getattr(r,'code',None)} {getattr(r,'message',None)}")
            delta = r.output.choices[0].message.content or ""
            if delta:
                yield delta

