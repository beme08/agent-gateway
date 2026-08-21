"""Tool registry: declarative schemas for every tool the agent can call.

Guardrail model — every tool carries a risk tier that the policy engine
enforces structurally, independent of the LLM, system prompt, caller role,
or approval flow:

  auto             agent may execute within tool constraints
  approval_required  agent may propose only; a human approves; policy is
                     re-evaluated at approval time before execution
  prohibited       neither agent nor human approval can execute it through
                   the gateway — denied unconditionally

Enforcement order (see policy.check):
  identity -> authorization -> prohibited gate -> scope rules ->
  argument validation -> quota -> [approval if required] -> execution
"""
from __future__ import annotations

from collections.abc import Awaitable, Callable
from dataclasses import dataclass, field
from typing import Any

RISK_TIERS = ("auto", "approval_required", "prohibited")


@dataclass
class ToolSchema:
    name: str
    description: str
    required_role: str
    parameters: dict  # JSON schema
    dangerous: bool = False  # legacy flag; superseded by risk_tier
    needs_manager_scope: bool = False
    risk_tier: str = "auto"
    # Argument constraints enforced by the policy engine BEFORE the executor
    # touches any adapter: {arg: {"enum": [...], "min": n, "max": n,
    # "max_length": n, "pattern": regex}}
    constraints: dict = field(default_factory=dict)


@dataclass
class ToolDef:
    schema: ToolSchema
    handler: Callable[..., Awaitable[dict]]


@dataclass
class ToolRegistry:
    _tools: dict[str, ToolDef] = field(default_factory=dict)

    def register(self, defn: ToolDef) -> None:
        self._tools[defn.schema.name] = defn

    def get(self, name: str) -> ToolDef | None:
        return self._tools.get(name)

    def list(self) -> list[ToolSchema]:
        return [d.schema for d in self._tools.values()]

    def as_cohere_tools(self) -> list[dict]:
        return [
            {
                "name": s.name,
                "description": s.description,
                "parameter_definitions": _schema_to_cohere(s.parameters),
            }
            for s in self.list()
        ]


def _schema_to_cohere(schema: dict) -> dict:
    out: dict[str, Any] = {}
    for k, v in schema.items():
        out[k] = {
            "description": v.get("description", ""),
            "type": v.get("type", "string"),
            "required": v.get("required", False),
        }
    return out
