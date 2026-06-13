"""Tool registry: declarative schemas for every tool the agent can call."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Awaitable, Callable


@dataclass
class ToolSchema:
    name: str
    description: str
    required_role: str
    parameters: dict  # JSON schema
    dangerous: bool = False
    needs_manager_scope: bool = False


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
