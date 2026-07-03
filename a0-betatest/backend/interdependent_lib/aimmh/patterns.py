# ratios: loc_comments=104:49 imports_exports=4:6 calls_definitions=34:7
# === MODULE_BUILD ===
# id: aimmh_patterns_impl
#   module_name: patterns
#   module_kind: engine
#   summary: pure-async multi-model orchestration patterns over call_fn(model_id, messages)
#   owner: a0p maintainer
#   public_surface: ModelResult, fan_out, daisy_chain, room_all, room_synthesized, council
#   internal_surface: _invoke, CallFn
#   auth_boundary: none
#   storage_boundary: none
#   network_boundary: none
#   user_data_boundary: none
#   admin_only: false
#   tests: a0p_skills.contracts.aimmh_invoke_propagates_error
#   rollout: default_enabled
#   rollback: revert file from git
# === END MODULE_BUILD ===
# === BOUNDARIES ===
# id: aimmh_patterns_impl_boundaries
#   summary: pure-async multi-model orchestration patterns over call_fn(model_id, messages)
#   auth_boundary: none
#   storage_boundary: none
#   network_boundary: none
#   user_data_boundary: none
#   admin_only: false
#   owner: a0p maintainer
# === END BOUNDARIES ===
# === CAPABILITIES ===
# id: aimmh_patterns_impl
#   summary: pure-async multi-model orchestration patterns over call_fn(model_id, messages)
#   exposes: ModelResult, fan_out, daisy_chain, room_all, room_synthesized, council
#   boundaries: auth:none, storage:none, network:none, user_data:none
#   owner: a0p maintainer
# === END CAPABILITIES ===
"""AIMMH interaction patterns — pure async, no external deps."""
from __future__ import annotations
import asyncio
from dataclasses import dataclass, field
from typing import Awaitable, Callable, Any


@dataclass
class ModelResult:
    model_id: str
    content: str
    usage: dict = field(default_factory=dict)
    error: str | None = None
    meta: dict = field(default_factory=dict)


CallFn = Callable[[str, list[dict]], Awaitable[Any]]
# call_fn returns either a string OR a dict {"content": ..., "usage": {...}}


async def _invoke(call_fn: CallFn, model_id: str, messages: list[dict]) -> ModelResult:
    try:
        r = await call_fn(model_id, messages)
        if isinstance(r, dict):
            return ModelResult(
                model_id=model_id,
                content=str(r.get("content", "")),
                usage=r.get("usage", {}) or {},
                meta=r.get("meta", {}) or {},
                error=r.get("error"),
            )
        return ModelResult(model_id=model_id, content=str(r))
    except Exception as e:
        return ModelResult(model_id=model_id, content="", error=str(e))


# === CONTRACTS ===
# id: aimmh_fan_out_parallel
#   given: N model_ids and one prompt
#   then:  all models called concurrently; one ModelResult per model returned in order
#   class: orchestration
#   call: a0p_skills.contracts.aimmh_invoke_propagates_error
# === END CONTRACTS ===
async def fan_out(
    call_fn: CallFn,
    model_ids: list[str],
    messages: list[dict],
) -> list[ModelResult]:
    """Send one prompt to N models in parallel."""
    tasks = [_invoke(call_fn, mid, messages) for mid in model_ids]
    return await asyncio.gather(*tasks)


async def daisy_chain(
    call_fn: CallFn,
    model_ids: list[str],
    messages: list[dict],
    rounds: int = 1,
) -> list[ModelResult]:
    """A → B → C sequentially for `rounds` cycles; each model sees the prior response."""
    out: list[ModelResult] = []
    current_messages = list(messages)
    chain = list(model_ids) * rounds
    for mid in chain:
        r = await _invoke(call_fn, mid, current_messages)
        out.append(r)
        # feed prior reply forward as an assistant message
        if r.content:
            current_messages = current_messages + [
                {"role": "assistant", "content": f"[{mid}]: {r.content}"},
                {"role": "user", "content": "Continue from the previous response. Refine, extend, or critique."},
            ]
    return out


async def room_all(
    call_fn: CallFn,
    model_ids: list[str],
    messages: list[dict],
    rounds: int = 2,
) -> list[list[ModelResult]]:
    """Round-based: each round every model sees every other's prior round responses."""
    history: list[list[ModelResult]] = []
    prior_text = ""
    for _round in range(rounds):
        round_msgs = list(messages)
        if prior_text:
            round_msgs.append({"role": "user", "content": f"Prior round responses from all models:\n{prior_text}\n\nNow respond again with your refined view."})
        results = await fan_out(call_fn, model_ids, round_msgs)
        history.append(results)
        prior_text = "\n\n".join(f"[{r.model_id}]: {r.content}" for r in results if r.content)
    return history


async def room_synthesized(
    call_fn: CallFn,
    model_ids: list[str],
    messages: list[dict],
    synth_model: str,
    rounds: int = 2,
) -> dict:
    """Each round: fan_out, then synthesize. Synthesis drives the next round."""
    rounds_data: list[dict] = []
    synth_so_far = ""
    for _round in range(rounds):
        round_msgs = list(messages)
        if synth_so_far:
            round_msgs.append({"role": "user", "content": f"Prior synthesis:\n{synth_so_far}\n\nRespond again."})
        results = await fan_out(call_fn, model_ids, round_msgs)
        synth_prompt = (
            "You are the synthesizer. Below are responses from multiple models to the same prompt. "
            "Synthesize them into one cohesive, accurate answer. Note disagreements explicitly.\n\n"
            + "\n\n".join(f"[{r.model_id}]: {r.content}" for r in results if r.content)
        )
        synth = await _invoke(call_fn, synth_model, [{"role": "user", "content": synth_prompt}])
        synth_so_far = synth.content
        rounds_data.append({"responses": results, "synthesis": synth})
    return {"rounds": rounds_data, "final": synth_so_far}


async def council(
    call_fn: CallFn,
    model_ids: list[str],
    prompt: str,
) -> list[ModelResult]:
    """Each model first sees all peer responses (including own first pass) and synthesizes."""
    base = [{"role": "user", "content": prompt}]
    first_pass = await fan_out(call_fn, model_ids, base)
    panel = "\n\n".join(f"[{r.model_id}]: {r.content}" for r in first_pass if r.content)
    synth_prompt = (
        f"Original prompt: {prompt}\n\nResponses from all council members (including yours):\n{panel}\n\n"
        "Synthesize a single best answer. Note where the council disagrees."
    )
    tasks = [_invoke(call_fn, mid, [{"role": "user", "content": synth_prompt}]) for mid in model_ids]
    return await asyncio.gather(*tasks)
# ratios: loc_comments=104:49 imports_exports=4:6 calls_definitions=34:7
