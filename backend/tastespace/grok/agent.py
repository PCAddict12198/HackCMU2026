"""Ask TasteSpace: a Grok tool-calling agent over the engine.

Grok decides WHICH engine tools to call and phrases the answer; the engine computes every number.
Replies that cite numbers the tools did not return are replaced by a deterministic template
(grounded=false). UI actions are derived from the tool trace, never invented by the model.
"""

import json

from pydantic import ValidationError
from tastespace_contracts.api_models import AskRequest, AskResponse, ToolCallTrace
from tastespace_contracts.taxonomy import DIM_IDS

from ..errors import TasteSpaceError
from ..state import EngineState
from .client import ChatFactory, ToolCall
from .errors import provider_error_message
from .grounding import derive_ui_actions, template_reply, ungrounded_numbers
from .tools import TOOLS, tool_specs

MAX_TOOL_ROUNDS = 4
MAX_CATALOG = 250  # dishes listed in the system prompt

SYSTEM_PROMPT = """You are the guide inside TasteSpace, a computational map of dishes built from ingredient
sensory profiles. You do NOT judge taste yourself.
Rules:
- Every similarity, percentile or sensory value you mention MUST appear in a tool result from this
  conversation. Never estimate, round creatively or invent numbers.
- Dishes in TasteSpace (dish_id: name, cuisine): {catalog}
  Use these dish_ids directly. Call search_dishes only if the user's dish is not clearly in this list.
- If a name fits several dishes (e.g. two ramens), use the most typical one, and say in the reply which one
  you used and which other one they can ask about.
- "flavor twin", "what tastes like X from another cuisine" -> find_twins.
- "like X but lighter / more acidic / spicier ..." -> shift_taste. Deltas are sigma units: slight 0.5,
  noticeable 1.0, strong 1.5-2.0; negative means less. Dimensions: {dims}.
  lighter -> rich negative; tangy/acidic -> sour; hotter -> spicy; soupier -> brothy; creamier -> creamy.
- "why" / "what do they share" -> explain_pair.
- Describe similarity as a percentile ("closer than 93% of dish pairs"). Keep replies under 80 words.
Context: {context}"""


def _system_prompt(req: AskRequest, state: EngineState) -> str:
    sel = req.context.selected_dish_id
    ctx = f"the user has '{state.dishes[sel].name}' (dish_id {sel}) selected." if sel in state.dishes else "nothing selected."
    # The catalog in the prompt saves a search_dishes round-trip (~2 s) per question; ids are still
    # validated by every tool. Very large spaces fall back to search.
    dishes = list(state.dishes.values())
    catalog = ("; ".join(f"{m.id}: {m.name} ({m.cuisine})" for m in dishes) if len(dishes) <= MAX_CATALOG
               else "(too many to list: use search_dishes)")
    return SYSTEM_PROMPT.format(dims=", ".join(DIM_IDS), context=ctx, catalog=catalog)


def _execute(call: ToolCall, state: EngineState, n: int) -> tuple[ToolCallTrace | None, str]:
    call_id = call.id or f"call_{n}"
    tool = TOOLS.get(call.name)
    if tool is None:
        return None, json.dumps({"error": f"unknown tool '{call.name}'. Available: {', '.join(TOOLS)}"})
    try:
        raw_args = json.loads(call.arguments or "{}")
    except json.JSONDecodeError:
        raw_args = {"_raw": call.arguments}
    try:
        args = tool.args_model.model_validate(raw_args)
        result = tool.run(state, args)
        entry = ToolCallTrace(call_id=call_id, tool=tool.name, args=args.model_dump(), ok=True, result=result)  # type: ignore[arg-type]
        return entry, json.dumps(result)
    except ValidationError as exc:
        msg = "; ".join(f"{'.'.join(map(str, e['loc']))}: {e['msg']}" for e in exc.errors())
    except TasteSpaceError as exc:
        msg = exc.message
    entry = ToolCallTrace(call_id=call_id, tool=tool.name, args=raw_args if isinstance(raw_args, dict) else {},  # type: ignore[arg-type]
                          ok=False, error=msg)
    return entry, json.dumps({"error": msg})


def run_ask(state: EngineState, req: AskRequest, chat_factory: ChatFactory) -> AskResponse:
    if req.messages[-1].role != "user":
        raise TasteSpaceError("validation_error", "the last message must come from the user")
    chat = chat_factory(_system_prompt(req, state), tool_specs())
    for msg in req.messages:
        (chat.add_user if msg.role == "user" else chat.add_assistant)(msg.content)

    trace: list[ToolCallTrace] = []
    reply = ""
    try:
        for rnd in range(MAX_TOOL_ROUNDS + 1):
            turn = chat.sample()
            if not turn.tool_calls:
                reply = turn.content.strip()
                break
            if rnd == MAX_TOOL_ROUNDS:
                break  # too many tool rounds: fall back to the template
            chat.add_turn(turn)
            for call in turn.tool_calls:
                entry, result_json = _execute(call, state, len(trace))
                if entry is not None:
                    trace.append(entry)
                chat.add_tool_result(call.id, result_json)
    except TasteSpaceError:
        raise
    except Exception as exc:  # network / provider errors
        reason = provider_error_message(exc)
        raise TasteSpaceError("grok_failed", f"Grok request failed: {reason}", {"reason": reason}) from exc

    user_text = " ".join(m.content for m in req.messages if m.role == "user")
    grounded = bool(reply) and not ungrounded_numbers(reply, trace, user_text)
    if not grounded:
        reply = template_reply(trace)
    return AskResponse(reply=reply, grounded=grounded, ui_actions=derive_ui_actions(trace, state), tool_trace=trace)
