"""Tool executor: dispatches a single tool call, wraps exceptions, returns
{ok, data, error} envelope."""
from __future__ import annotations

import time
from typing import Any

from .registry import ToolDef


async def execute(tool_def: ToolDef, arguments: dict, context: dict) -> dict:
    start = time.time()
    try:
        result = await tool_def.handler(arguments=arguments, context=context)
        latency = int((time.time() - start) * 1000)
        return {"ok": True, "data": result, "error": None, "latency_ms": latency}
    except Exception as e:
        latency = int((time.time() - start) * 1000)
        return {"ok": False, "data": None, "error": str(e), "latency_ms": latency}
