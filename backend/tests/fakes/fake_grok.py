"""Scripted stand-in for Grok so agent tests never touch the network."""

import json

from tastespace.grok.client import ModelTurn, ToolCall


class FakeChat:
    def __init__(self, script: list[ModelTurn], parse_result: dict | None = None):
        self.script = list(script)
        self.parse_result = parse_result
        self.log: list[tuple] = []
        self.system_prompt = ""
        self.tools = None

    def add_user(self, text: str) -> None:
        self.log.append(("user", text))

    def add_assistant(self, text: str) -> None:
        self.log.append(("assistant", text))

    def sample(self) -> ModelTurn:
        return self.script.pop(0) if self.script else ModelTurn(content="")

    def add_turn(self, turn: ModelTurn) -> None:
        self.log.append(("turn", turn))

    def add_tool_result(self, call_id: str, result: str) -> None:
        self.log.append(("tool", call_id, result))

    def parse(self, shape):
        return shape.model_validate(self.parse_result or {})


def fake_factory(script: list[ModelTurn], parse_result: dict | None = None):
    chats: list[FakeChat] = []

    def factory(system_prompt, tools=None):
        chat = FakeChat(script, parse_result)
        chat.system_prompt, chat.tools = system_prompt, tools
        chats.append(chat)
        return chat

    factory.chats = chats  # type: ignore[attr-defined]
    return factory


def call(name: str, args: dict, call_id: str = "c1") -> ToolCall:
    return ToolCall(id=call_id, name=name, arguments=json.dumps(args))


def tool_turn(*calls: ToolCall) -> ModelTurn:
    return ModelTurn(content="", tool_calls=list(calls))


def text_turn(text: str) -> ModelTurn:
    return ModelTurn(content=text)
