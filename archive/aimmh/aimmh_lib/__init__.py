# ratios: loc_comments=24:41 imports_exports=4:1 calls_definitions=5:0
"""
aimmh_lib — Async multi-model conversation orchestration library.

Standalone, framework-agnostic, zero external dependencies (stdlib + asyncio).
No FastAPI, MongoDB, or auth required.

Install:
    pip install aimmh-lib           # from PyPI (once published)
    pip install -e /path/to/aimmh   # editable local install from repo root

Quick start (with the aimmh backend adapter):
    import sys
    sys.path.insert(0, "/path/to/aimmh/backend")

    from aimmh_lib import daisy_chain, roleplay, council, ModelResult
    from aimmh_lib.adapters import make_call_fn

    call = make_call_fn(user={"api_keys": {}})  # uses EMERGENT_LLM_KEY env

    # Chain: GPT → Claude → Gemini, each building on the last
    results = await daisy_chain(call, ["gpt-4o", "claude-haiku-4-5-20251001", "gemini-2.0-flash"], "Explain gravity")

    # Roleplay: DM narrates, players act in initiative order
    results = await roleplay(
        call,
        player_models=["gpt-4o", "claude-haiku-4-5-20251001", "gemini-2.0-flash"],
        initial_prompt="You stand at the entrance to a dungeon.",
        dm_model="claude-4-sonnet-20250514",
        rounds=3,
        use_initiative=True,
        allow_reactions=True,
        action_word_limit=80,
    )

    # Council: every model synthesizes all responses including its own
    results = await council(call, ["gpt-4o", "claude-haiku-4-5-20251001", "gemini-2.0-flash"], "What is consciousness?")

Patterns (functional API):
    fan_out          — parallel call to N models (building block)
    daisy_chain      — A → output → B's prompt → C's prompt ...
    room_all         — all models respond, see each other, respond again
    room_synthesized — all respond, one synthesizer combines, synthesis drives next round
    council          — all respond, each synthesizes all responses (incl. own), in parallel
    roleplay         — DM + players, initiative ordering, sequential turns, optional reactions

Instantiation API:
    MultiModelHub    — bind a CallFn once, call any pattern as a method
    ModelInstance    — a single model as a stateful object with persistent history

Note: aimmh_lib.adapters is NOT imported here to avoid pulling in backend dependencies.
Import it explicitly: from aimmh_lib.adapters import make_call_fn
"""

from aimmh_lib.conversations import (
    ModelResult,
    CallFn,
    MultiModelHub,
    ModelInstance,
    fan_out,
    daisy_chain,
    room_all,
    room_synthesized,
    council,
    roleplay,
)

__all__ = [
    "ModelResult",
    "CallFn",
    "MultiModelHub",
    "ModelInstance",
    "fan_out",
    "daisy_chain",
    "room_all",
    "room_synthesized",
    "council",
    "roleplay",
]
# ratios: loc_comments=24:41 imports_exports=4:1 calls_definitions=5:0
