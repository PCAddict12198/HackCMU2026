"""The only place the backend talks to xAI (official `xai_sdk`). Everything else uses the
provider-neutral GrokChat protocol below, so tests run on scripted fakes with no network.

Configure with XAI_API_KEY + GROK_MODEL in .env (pick the model from https://docs.x.ai/docs/models).
"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass, field
from typing import Any, Protocol, TypeVar

from pydantic import BaseModel

from ..config import Settings, get_settings
from ..errors import TasteSpaceError

T = TypeVar("T", bound=BaseModel)


@dataclass
class ToolSpec:
    name: str
    description: str
    parameters: dict  # JSON Schema object


@dataclass
class ToolCall:
    id: str
    name: str
    arguments: str  # JSON text produced by the model


@dataclass
class ModelTurn:
    content: str
    tool_calls: list[ToolCall] = field(default_factory=list)
    raw: Any = None  # provider response object, appended back into the conversation


class GrokChat(Protocol):
    def add_user(self, text: str) -> None: ...
    def add_assistant(self, text: str) -> None: ...
    def sample(self) -> ModelTurn: ...
    def add_turn(self, turn: ModelTurn) -> None: ...
    def add_tool_result(self, call_id: str, result: str) -> None: ...
    def parse(self, shape: type[T]) -> T: ...


ChatFactory = Callable[[str, list[ToolSpec] | None], GrokChat]


class XaiChat:
    """GrokChat backed by xai_sdk (Client.chat.create / append / sample / parse)."""

    def __init__(self, client: Any, model: str, system_prompt: str, tools: list[ToolSpec] | None):
        from xai_sdk.chat import system, tool

        kwargs: dict[str, Any] = {}
        if tools:
            kwargs["tools"] = [tool(name=t.name, description=t.description, parameters=t.parameters) for t in tools]
            kwargs["tool_choice"] = "auto"
        self._chat = client.chat.create(model=model, messages=[system(system_prompt)], **kwargs)

    def add_user(self, text: str) -> None:
        from xai_sdk.chat import user

        self._chat.append(user(text))

    def add_assistant(self, text: str) -> None:
        from xai_sdk.chat import assistant

        self._chat.append(assistant(text))

    def sample(self) -> ModelTurn:
        resp = self._chat.sample()
        calls = [ToolCall(id=getattr(tc, "id", "") or f"call_{i}", name=tc.function.name,
                          arguments=tc.function.arguments or "{}") for i, tc in enumerate(resp.tool_calls)]
        return ModelTurn(content=resp.content or "", tool_calls=calls, raw=resp)

    def add_turn(self, turn: ModelTurn) -> None:
        self._chat.append(turn.raw)

    def add_tool_result(self, call_id: str, result: str) -> None:
        from xai_sdk.chat import tool_result

        self._chat.append(tool_result(result, tool_call_id=call_id))

    def parse(self, shape: type[T]) -> T:
        _, obj = self._chat.parse(shape)
        return obj


def xai_chat_factory(settings: Settings | None = None) -> ChatFactory:
    s = settings or get_settings()
    if not s.grok_configured:
        raise TasteSpaceError("grok_unavailable", "Grok is not configured: set XAI_API_KEY and GROK_MODEL in .env")
    from xai_sdk import Client

    client = Client(api_key=s.xai_api_key, timeout=30)
    model = s.grok_model or ""

    def factory(system_prompt: str, tools: list[ToolSpec] | None = None) -> GrokChat:
        return XaiChat(client, model, system_prompt, tools)

    return factory
