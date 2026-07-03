# ratios: loc_comments=490:186 imports_exports=6:9 calls_definitions=125:26
"""
conversations.py — Async multi-model conversation orchestration primitives.

All functions are pure async — no FastAPI, MongoDB, auth, or framework deps.
The only dependency is Python stdlib + asyncio.

The core insight: async is the library's reason for being. fan_out uses
asyncio.gather for true parallel calls; sequential patterns (daisy_chain,
roleplay) use await so each step can depend on the last. Callers compose
these freely without the backend's HTTP/DB overhead.

CallFn contract: async (model_id: str, messages: list[dict]) -> str
  - messages follows the OpenAI role format: [{"role": "user"|"assistant"|"system", "content": str}]
  - returns the full response string (adapters handle streaming → complete)
  - on error, returns a string starting with "[ERROR]"

Slot context design:
  slot_contexts is a list[Optional[str]] aligned by index with model_ids (or player_models).
  This allows calling the same model multiple times with different system prompts:
      model_ids     = ["gpt-4o", "gpt-4o"]
      slot_contexts = ["You are a critic.", "You are a defender."]
  ModelResult.slot_idx carries the position back so callers can cross-reference.
"""

from __future__ import annotations

import asyncio
import random
import time
from dataclasses import dataclass, field
from typing import Callable, Coroutine, Optional

# ---------------------------------------------------------------------------
# Public types
# ---------------------------------------------------------------------------

# async fn(model_id, messages) -> complete response string
CallFn = Callable[[str, list[dict]], Coroutine[None, None, str]]


@dataclass
class ModelResult:
    """A single model response within a conversation pattern.

    step_num=-1 is a sentinel for synthesis/DM steps that sit between rounds.
    Filter helpers:
        responses only:   [r for r in results if r.step_num >= 0]
        synthesis/DM:     [r for r in results if r.step_num == -1]
        by round:         [r for r in results if r.round_num == n]
        by slot:          [r for r in results if r.slot_idx == i]
    """
    model: str
    content: str
    response_time_ms: int = 0
    error: Optional[str] = None
    round_num: int = 0       # 0-indexed round
    step_num: int = 0        # 0-indexed step within round; -1 = synthesis/DM narration
    initiative: int = 0      # initiative roll (roleplay); 0 for non-roleplay patterns
    role: str = "player"     # "player" | "dm" | "synthesizer" | "council" | "reaction"
    slot_idx: int = 0        # index into original model_ids / player_models list


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _inject_system(
    messages: list[dict],
    slot_idx: int,
    slot_contexts: Optional[list[Optional[str]]],
) -> list[dict]:
    """Prepend {"role": "system", "content": ...} if slot_contexts has an entry at slot_idx."""
    if not slot_contexts or slot_idx >= len(slot_contexts):
        return messages
    sys_str = slot_contexts[slot_idx]
    if not sys_str:
        return messages
    return [{"role": "system", "content": sys_str}] + messages


def _trim(history: list[dict], max_history: int) -> list[dict]:
    """Keep the last max_history messages (pairs = 2 items each)."""
    return history[-max_history:] if len(history) > max_history else history


async def _call(
    call: CallFn,
    model_id: str,
    messages: list[dict],
    slot_contexts: Optional[list[Optional[str]]],
    slot_idx: int,
    round_num: int,
    step_num: int,
    role: str = "player",
    initiative: int = 0,
) -> ModelResult:
    """Single timed call with error capture."""
    msgs = _inject_system(messages, slot_idx, slot_contexts)
    t = time.monotonic()
    try:
        content = await call(model_id, msgs)
    except Exception as e:
        content = f"[ERROR] {e}"
    elapsed_ms = int((time.monotonic() - t) * 1000)
    return ModelResult(
        model=model_id,
        content=content,
        response_time_ms=elapsed_ms,
        error=content if content.startswith("[ERROR]") else None,
        round_num=round_num,
        step_num=step_num,
        initiative=initiative,
        role=role,
        slot_idx=slot_idx,
    )


# ---------------------------------------------------------------------------
# fan_out — parallel building block
# ---------------------------------------------------------------------------

async def fan_out(
    call: CallFn,
    model_ids: list[str],
    messages: list[dict],
    slot_contexts: Optional[list[Optional[str]]] = None,
    round_num: int = 0,
    step_num: int = 0,
) -> list[ModelResult]:
    """Call all models in parallel with the same messages.

    This is the async core: asyncio.gather fires all calls concurrently.
    Returns results in model_ids order. slot_idx = position in model_ids.
    """
    return list(await asyncio.gather(*[
        _call(call, m, messages, slot_contexts, i, round_num, step_num)
        for i, m in enumerate(model_ids)
    ]))


# ---------------------------------------------------------------------------
# daisy_chain — sequential A → B → C
# ---------------------------------------------------------------------------

async def daisy_chain(
    call: CallFn,
    model_ids: list[str],
    prompt: str,
    rounds: int = 1,
    slot_contexts: Optional[list[Optional[str]]] = None,
    include_original_prompt: bool = True,
    max_history: int = 30,
) -> list[ModelResult]:
    """Sequential chain: each model's response becomes the next model's prompt.

    Round 0, step 0: raw prompt → model[0].
    All subsequent steps:
        [Chain Round {r+1}, Step {s+1}]
        Previous response from {prev_model}: {content}
        Original prompt: {prompt}   ← if include_original_prompt

    History accumulates so each step has full prior context.
    slot_idx = step position within each round (0 for model[0], 1 for model[1], ...).
    """
    all_results: list[ModelResult] = []
    history: list[dict] = []
    last_content = prompt
    last_model = "user"

    for round_num in range(rounds):
        for step_num, (slot_idx, model_id) in enumerate(enumerate(model_ids)):
            if round_num == 0 and step_num == 0:
                prompt_text = prompt
            else:
                prompt_text = (
                    f"[Chain Round {round_num + 1}, Step {step_num + 1}]\n\n"
                    f"Previous response from {last_model}:\n{last_content}"
                )
                if include_original_prompt:
                    prompt_text += f"\n\nOriginal prompt: {prompt}"

            messages = _trim(history, max_history) + [{"role": "user", "content": prompt_text}]
            result = await _call(call, model_id, messages, slot_contexts, slot_idx, round_num, step_num)
            all_results.append(result)

            history.append({"role": "user", "content": prompt_text})
            history.append({"role": "assistant", "content": result.content})
            last_content = result.content
            last_model = model_id

    return all_results


# ---------------------------------------------------------------------------
# room_all — every model sees all others' responses
# ---------------------------------------------------------------------------

async def room_all(
    call: CallFn,
    model_ids: list[str],
    prompt: str,
    rounds: int = 1,
    slot_contexts: Optional[list[Optional[str]]] = None,
    max_history: int = 30,
) -> list[ModelResult]:
    """Shared room: all models respond, then each sees all responses, responds again.

    Round 0: parallel fan_out with raw prompt.
    Round 1+: each model receives:
        [ROUND {r+1} — respond after seeing other models' responses]
        Response from {model_a}: {content}
        ---
        Response from {model_b}: {content}
        Original prompt: {prompt}

    Single shared history (all models in the same room context).
    """
    all_results: list[ModelResult] = []
    shared_history: list[dict] = []

    for round_num in range(rounds):
        if round_num == 0:
            user_turn = {"role": "user", "content": prompt}
            messages = _trim(shared_history, max_history) + [user_turn]
            round_results = await fan_out(call, model_ids, messages, slot_contexts, round_num=0)
        else:
            prev_round = all_results[-(len(model_ids)):]
            share_text = f"[ROUND {round_num + 1} — respond after seeing other models' responses]\n\n"
            share_text += "\n\n---\n\n".join(
                f"Response from {r.model}:\n{r.content}"
                for r in prev_round if not r.error
            )
            share_text += f"\n\nOriginal prompt: {prompt}"

            user_turn = {"role": "user", "content": share_text}
            messages = _trim(shared_history, max_history) + [user_turn]
            round_results = list(await asyncio.gather(*[
                _call(call, m, messages, slot_contexts, i, round_num, step_num=0)
                for i, m in enumerate(model_ids)
            ]))

        all_results.extend(round_results)

        # Shared history: one user turn + all assistant responses
        shared_history.append(user_turn)
        for r in round_results:
            shared_history.append({"role": "assistant", "content": r.content})

    return all_results


# ---------------------------------------------------------------------------
# room_synthesized — one synthesizer combines responses, drives next round
# ---------------------------------------------------------------------------

async def room_synthesized(
    call: CallFn,
    model_ids: list[str],
    prompt: str,
    synthesis_model: str,
    rounds: int = 1,
    synthesis_prompt: str = "Synthesize and analyze these AI responses:",
    slot_contexts: Optional[list[Optional[str]]] = None,
    synth_slot_context: Optional[str] = None,
    max_history: int = 30,
) -> list[ModelResult]:
    """All models respond in parallel; one synthesis model combines them.

    Round 0: parallel fan_out.
    Synthesis (step_num=-1): synthesis_model receives:
        [ROUND {r+1} SYNTHESIS]
        {synthesis_prompt}
        Response from {model_a}: {content}
        ---
        Response from {model_b}: {content}
    Round 1+: models respond to synthesis:
        [ROUND {r+1} — respond to the synthesis]
        Synthesis by {synthesis_model}: {synth_content}
        Original prompt: {prompt}

    synthesis_model results have step_num=-1.
    Filter: [r for r in results if r.step_num >= 0] → player responses only.
    synth_slot_context: optional system prompt for the synthesis model specifically.
    """
    if not synthesis_model:
        raise ValueError("synthesis_model is required")

    # Synthesis model gets slot_idx = len(model_ids) (just beyond the player slots)
    synth_slot_idx = len(model_ids)
    synth_contexts = (slot_contexts or []) + [synth_slot_context]

    all_results: list[ModelResult] = []
    shared_history: list[dict] = []

    for round_num in range(rounds):
        # --- player round ---
        if round_num == 0:
            user_turn = {"role": "user", "content": prompt}
        else:
            prev_synth = next(
                (r for r in reversed(all_results) if r.step_num == -1), None
            )
            next_prompt = (
                f"[ROUND {round_num + 1} — respond to the synthesis]\n\n"
                f"Synthesis by {synthesis_model}:\n{prev_synth.content}\n\n"
                f"Original prompt: {prompt}"
            ) if prev_synth else prompt
            user_turn = {"role": "user", "content": next_prompt}

        messages = _trim(shared_history, max_history) + [user_turn]
        round_results = list(await asyncio.gather(*[
            _call(call, m, messages, slot_contexts, i, round_num, step_num=0, role="player")
            for i, m in enumerate(model_ids)
        ]))
        all_results.extend(round_results)
        shared_history.append(user_turn)
        for r in round_results:
            shared_history.append({"role": "assistant", "content": r.content})

        # --- synthesis step ---
        synth_input = "\n\n---\n\n".join(
            f"Response from {r.model}:\n{r.content}"
            for r in round_results if not r.error
        )
        synth_turn = {"role": "user", "content": (
            f"[ROUND {round_num + 1} SYNTHESIS]\n"
            f"{synthesis_prompt}\n\n{synth_input}"
        )}
        synth_messages = _trim(shared_history, max_history) + [synth_turn]
        synth_result = await _call(
            call, synthesis_model, synth_messages, synth_contexts,
            synth_slot_idx, round_num, step_num=-1, role="synthesizer"
        )
        all_results.append(synth_result)
        shared_history.append(synth_turn)
        shared_history.append({"role": "assistant", "content": synth_result.content})

    return all_results


# ---------------------------------------------------------------------------
# council — every model synthesizes all responses (including its own)
# ---------------------------------------------------------------------------

async def council(
    call: CallFn,
    model_ids: list[str],
    prompt: str,
    rounds: int = 1,
    synthesis_prompt: str = "Synthesize and analyze all model responses including your own:",
    slot_contexts: Optional[list[Optional[str]]] = None,
    max_history: int = 30,
) -> list[ModelResult]:
    """Each model produces its own synthesis of all responses in parallel.

    Round 0 (step_num=0): parallel fan_out with raw prompt.
    Synthesis round (step_num=1): each model receives ALL round responses
        (including its own) and synthesizes them concurrently:
        [COUNCIL SYNTHESIS — ROUND {r+1}]
        {synthesis_prompt}
        Response from {model_a}: {content}
        ---
        Response from {model_b}: {content}
    Round 1+ uses prior synthesis outputs as context.

    step_num=0 → initial responses; step_num=1 → synthesis responses.
    """
    all_results: list[ModelResult] = []
    shared_history: list[dict] = []

    for round_num in range(rounds):
        # --- initial responses ---
        if round_num == 0:
            user_turn = {"role": "user", "content": prompt}
        else:
            prev_syntheses = [
                r for r in all_results
                if r.round_num == round_num - 1 and r.step_num == 1
            ]
            council_context = "\n\n---\n\n".join(
                f"Synthesis by {r.model}:\n{r.content}"
                for r in prev_syntheses if not r.error
            )
            user_turn = {"role": "user", "content": (
                f"[COUNCIL ROUND {round_num + 1}]\n\n"
                f"Prior syntheses:\n\n{council_context}\n\n"
                f"Original prompt: {prompt}"
            )}

        messages = _trim(shared_history, max_history) + [user_turn]
        round_results = list(await asyncio.gather(*[
            _call(call, m, messages, slot_contexts, i, round_num, step_num=0, role="council")
            for i, m in enumerate(model_ids)
        ]))
        all_results.extend(round_results)
        shared_history.append(user_turn)
        for r in round_results:
            shared_history.append({"role": "assistant", "content": r.content})

        # --- each model synthesizes all responses in parallel ---
        all_responses_text = "\n\n---\n\n".join(
            f"Response from {r.model}:\n{r.content}"
            for r in round_results if not r.error
        )
        synth_turn = {"role": "user", "content": (
            f"[COUNCIL SYNTHESIS — ROUND {round_num + 1}]\n"
            f"{synthesis_prompt}\n\n{all_responses_text}"
        )}
        synth_messages = _trim(shared_history, max_history) + [synth_turn]

        # All models synthesize concurrently — this is the async payoff
        synth_results = list(await asyncio.gather(*[
            _call(call, m, synth_messages, slot_contexts, i, round_num, step_num=1, role="council")
            for i, m in enumerate(model_ids)
        ]))
        all_results.extend(synth_results)
        shared_history.append(synth_turn)
        for r in synth_results:
            shared_history.append({"role": "assistant", "content": r.content})

    return all_results


# ---------------------------------------------------------------------------
# roleplay — DM narrates, players act in initiative order, reactions supported
# ---------------------------------------------------------------------------

async def roleplay(
    call: CallFn,
    player_models: list[str],
    initial_prompt: str,
    dm_model: Optional[str] = None,
    dm_rotation: Optional[list[str]] = None,
    rounds: int = 1,
    slot_contexts: Optional[list[Optional[str]]] = None,
    dm_slot_context: Optional[str] = None,
    dm_rotation_contexts: Optional[list[Optional[str]]] = None,
    action_word_limit: Optional[int] = None,
    use_initiative: bool = True,
    allow_reactions: bool = False,
    max_history: int = 30,
) -> list[ModelResult]:
    """DM-driven roleplay: initiative ordering, sequential player turns, optional reactions.

    Structure per round:
      1. Initiative roll (random) determines player turn order for this round.
      2. Players act sequentially in initiative order. Each player sees:
           - DM's narration from the prior round (or initial_prompt for round 0)
           - Actions of players who have already acted this round
      3. If allow_reactions=True: after each player acts, remaining players
           may react (a brief interrupt response) before the next player goes.
      4. DM sees all player actions → narrates outcome (step_num=-1).
         DM narration drives the next round.

    DM selection:
      - dm_model: fixed DM for all rounds (context from dm_slot_context)
      - dm_rotation: list of model IDs that cycle as DM each round
                     (contexts from dm_rotation_contexts, aligned by index)
      - If neither, the first player_model acts as DM each round

    slot_contexts: system prompts for player_models (index-aligned, handles duplicates).
    dm_slot_context: system prompt for a fixed dm_model.
    dm_rotation_contexts: system prompts for each DM in dm_rotation (index-aligned).

    action_word_limit: injects "Respond in {N} words or fewer." into each
        player's prompt (token economy, like action economy in TTRPGs).

    Returns all ModelResult objects. Use role field to filter:
        players:   [r for r in results if r.role == "player"]
        dm turns:  [r for r in results if r.role == "dm"]
        reactions: [r for r in results if r.role == "reaction"]
    """
    if dm_rotation and dm_model:
        raise ValueError("Provide dm_model or dm_rotation, not both")

    all_results: list[ModelResult] = []
    shared_history: list[dict] = []
    dm_narration = initial_prompt  # seeds round 0

    # player slots: list of (slot_idx, model_id) — preserves duplicates
    player_slots_list: list[tuple[int, str]] = list(enumerate(player_models))

    def _get_dm_info(round_num: int) -> tuple[str, Optional[str]]:
        """Returns (model_id, system_context) for the DM this round."""
        if dm_rotation:
            idx = round_num % len(dm_rotation)
            ctx = (dm_rotation_contexts[idx] if dm_rotation_contexts and idx < len(dm_rotation_contexts) else None)
            return dm_rotation[idx], ctx
        if dm_model:
            return dm_model, dm_slot_context
        # First player acts as DM
        return player_models[0], (slot_contexts[0] if slot_contexts else None)

    def _active_player_slots(round_num: int) -> list[tuple[int, str]]:
        """Player (slot_idx, model_id) pairs excluding the DM for this round."""
        dm_id, _ = _get_dm_info(round_num)
        # If neither dm_model nor dm_rotation, the first player slot is DM
        if not dm_model and not dm_rotation:
            return player_slots_list[1:]
        return player_slots_list

    def _word_limit_suffix() -> str:
        if action_word_limit:
            return f"\n\nRespond in {action_word_limit} words or fewer."
        return ""

    for round_num in range(rounds):
        dm_id, dm_ctx = _get_dm_info(round_num)
        active_players = _active_player_slots(round_num)

        # --- initiative: random roll per slot, descending order ---
        if use_initiative:
            rolls = {slot_idx: random.randint(1, 20) for slot_idx, _ in active_players}
            ordered_players = sorted(active_players, key=lambda t: rolls[t[0]], reverse=True)
        else:
            rolls = {slot_idx: 0 for slot_idx, _ in active_players}
            ordered_players = active_players

        round_actions: list[ModelResult] = []

        # --- sequential player turns in initiative order ---
        for step_num, (slot_idx, player) in enumerate(ordered_players):
            prior_actions = "\n\n".join(
                f"{r.model} acted:\n{r.content}"
                for r in round_actions if not r.error
            )
            if round_actions:
                player_prompt = (
                    f"[ROUND {round_num + 1} — your turn (initiative {rolls[slot_idx]})]\n\n"
                    f"DM: {dm_narration}\n\n"
                    f"Actions so far this round:\n{prior_actions}"
                    f"{_word_limit_suffix()}"
                )
            else:
                player_prompt = (
                    f"[ROUND {round_num + 1} — your turn (initiative {rolls[slot_idx]}, going first)]\n\n"
                    f"DM: {dm_narration}"
                    f"{_word_limit_suffix()}"
                )

            messages = _trim(shared_history, max_history) + [
                {"role": "user", "content": player_prompt}
            ]
            result = await _call(
                call, player, messages, slot_contexts, slot_idx,
                round_num, step_num, role="player", initiative=rolls[slot_idx]
            )
            round_actions.append(result)
            all_results.append(result)

            shared_history.append({"role": "user", "content": player_prompt})
            shared_history.append({"role": "assistant", "content": result.content})

            # --- reactions: remaining players can react to this action ---
            if allow_reactions and not result.error:
                acted_slots = {r.slot_idx for r in round_actions}
                remaining = [(si, pm) for si, pm in ordered_players if si not in acted_slots]
                if remaining:
                    reaction_prompt = (
                        f"[ROUND {round_num + 1} — REACTION to {player}'s action]\n\n"
                        f"{player} acted: {result.content}\n\n"
                        f"Do you wish to react? If so, describe your reaction briefly."
                        f"{_word_limit_suffix()}"
                    )
                    reaction_messages = _trim(shared_history, max_history) + [
                        {"role": "user", "content": reaction_prompt}
                    ]
                    reactions = list(await asyncio.gather(*[
                        _call(
                            call, pm, reaction_messages, slot_contexts, si,
                            round_num, step_num=step_num, role="reaction",
                            initiative=rolls.get(si, 0)
                        )
                        for si, pm in remaining
                    ]))
                    all_results.extend(reactions)
                    shared_history.append({"role": "user", "content": reaction_prompt})
                    for rx in reactions:
                        shared_history.append({"role": "assistant", "content": rx.content})

        # --- DM narrates outcome (step_num=-1) ---
        all_actions_text = "\n\n".join(
            f"{r.model} (initiative {r.initiative}): {r.content}"
            for r in round_actions if not r.error
        )
        reactions_this_round = [r for r in all_results if r.round_num == round_num and r.role == "reaction"]
        reactions_text = ""
        if reactions_this_round:
            reactions_text = "\n\nReactions:\n" + "\n\n".join(
                f"{r.model} reacted: {r.content}"
                for r in reactions_this_round if not r.error
            )

        dm_prompt = (
            f"[ROUND {round_num + 1} — DM NARRATION]\n\n"
            f"Player actions this round:\n{all_actions_text}"
            f"{reactions_text}\n\n"
            f"Narrate the outcome and set up the next scene."
        )
        dm_messages = _trim(shared_history, max_history) + [
            {"role": "user", "content": dm_prompt}
        ]
        # DM slot_idx = len(player_models) (beyond all player slots)
        dm_slot_idx = len(player_models)
        dm_contexts = (slot_contexts or []) + [dm_ctx]
        dm_result = await _call(
            call, dm_id, dm_messages, dm_contexts,
            dm_slot_idx, round_num, step_num=-1, role="dm"
        )
        all_results.append(dm_result)
        shared_history.append({"role": "user", "content": dm_prompt})
        shared_history.append({"role": "assistant", "content": dm_result.content})
        dm_narration = dm_result.content  # seeds next round

    return all_results


# ---------------------------------------------------------------------------
# MultiModelHub — instantiation-based API (binds call_fn once)
# ---------------------------------------------------------------------------

class MultiModelHub:
    """Instantiation-based wrapper around all orchestration patterns.

    Bind a CallFn once at construction time, then call any pattern as a method
    without repeating the call argument.

    Example::

        hub = MultiModelHub(call_fn)
        results = await hub.fan_out(["gpt-4o", "claude-haiku-4-5-20251001"], messages)
        results = await hub.daisy_chain(["gpt-4o", "claude-haiku-4-5-20251001"], "Explain gravity")
        results = await hub.council(["gpt-4o", "claude-haiku-4-5-20251001"], "What is consciousness?")

    All keyword arguments are forwarded to the underlying function unchanged.
    """

    def __init__(self, call: CallFn) -> None:
        self.call = call

    async def fan_out(
        self,
        model_ids: list[str],
        messages: list[dict],
        slot_contexts: Optional[list[Optional[str]]] = None,
        round_num: int = 0,
        step_num: int = 0,
    ) -> list[ModelResult]:
        return await fan_out(self.call, model_ids, messages, slot_contexts, round_num, step_num)

    async def daisy_chain(
        self,
        model_ids: list[str],
        prompt: str,
        rounds: int = 1,
        slot_contexts: Optional[list[Optional[str]]] = None,
        include_original_prompt: bool = True,
        max_history: int = 30,
    ) -> list[ModelResult]:
        return await daisy_chain(self.call, model_ids, prompt, rounds, slot_contexts, include_original_prompt, max_history)

    async def room_all(
        self,
        model_ids: list[str],
        prompt: str,
        rounds: int = 1,
        slot_contexts: Optional[list[Optional[str]]] = None,
        max_history: int = 30,
    ) -> list[ModelResult]:
        return await room_all(self.call, model_ids, prompt, rounds, slot_contexts, max_history)

    async def room_synthesized(
        self,
        model_ids: list[str],
        prompt: str,
        synthesis_model: str,
        rounds: int = 1,
        synthesis_prompt: str = "Synthesize and analyze these AI responses:",
        slot_contexts: Optional[list[Optional[str]]] = None,
        synth_slot_context: Optional[str] = None,
        max_history: int = 30,
    ) -> list[ModelResult]:
        return await room_synthesized(self.call, model_ids, prompt, synthesis_model, rounds, synthesis_prompt, slot_contexts, synth_slot_context, max_history)

    async def council(
        self,
        model_ids: list[str],
        prompt: str,
        rounds: int = 1,
        synthesis_prompt: str = "Synthesize and analyze all model responses including your own:",
        slot_contexts: Optional[list[Optional[str]]] = None,
        max_history: int = 30,
    ) -> list[ModelResult]:
        return await council(self.call, model_ids, prompt, rounds, synthesis_prompt, slot_contexts, max_history)

    async def roleplay(
        self,
        player_models: list[str],
        initial_prompt: str,
        dm_model: Optional[str] = None,
        dm_rotation: Optional[list[str]] = None,
        rounds: int = 1,
        slot_contexts: Optional[list[Optional[str]]] = None,
        dm_slot_context: Optional[str] = None,
        dm_rotation_contexts: Optional[list[Optional[str]]] = None,
        action_word_limit: Optional[int] = None,
        use_initiative: bool = True,
        allow_reactions: bool = False,
        max_history: int = 30,
    ) -> list[ModelResult]:
        return await roleplay(self.call, player_models, initial_prompt, dm_model, dm_rotation, rounds, slot_contexts, dm_slot_context, dm_rotation_contexts, action_word_limit, use_initiative, allow_reactions, max_history)


# ---------------------------------------------------------------------------
# ModelInstance — a single model as a semi-permanent stateful object
# ---------------------------------------------------------------------------

class ModelInstance:
    """A single model with persistent conversation history.

    Encapsulates a model_id, an optional system prompt, and an accumulating
    message history so callers can hold a long-running conversation without
    managing the history list themselves.

    Example::

        gpt = ModelInstance(call_fn, "gpt-4o", system_context="You are a Socratic tutor.")
        r1 = await gpt.send("What is entropy?")
        r2 = await gpt.send("Give me an example.")   # history carries over
        print(gpt.history)                            # full message log
        gpt.clear()                                   # reset to fresh state

    Args:
        call:           The async CallFn backend.
        model_id:       The model identifier string (e.g. "gpt-4o").
        system_context: Optional system prompt prepended to every call.
        max_history:    Maximum number of messages to retain (rolling window).
    """

    def __init__(
        self,
        call: CallFn,
        model_id: str,
        system_context: Optional[str] = None,
        max_history: int = 30,
    ) -> None:
        self.call = call
        self.model_id = model_id
        self.system_context = system_context
        self.max_history = max_history
        self._history: list[dict] = []

    @property
    def history(self) -> list[dict]:
        """Read-only view of the current message history (no system prompt)."""
        return list(self._history)

    def clear(self) -> None:
        """Reset conversation history to a fresh state."""
        self._history = []

    async def send(self, message: str) -> ModelResult:
        """Send a user message and return the model's response.

        The user message and the model's reply are appended to history so
        subsequent calls have full context.
        """
        user_turn = {"role": "user", "content": message}
        trimmed = _trim(self._history, self.max_history)
        msgs = trimmed + [user_turn]
        if self.system_context:
            msgs = [{"role": "system", "content": self.system_context}] + msgs

        t = time.monotonic()
        try:
            content = await self.call(self.model_id, msgs)
        except Exception as e:
            content = f"[ERROR] {e}"
        elapsed_ms = int((time.monotonic() - t) * 1000)

        result = ModelResult(
            model=self.model_id,
            content=content,
            response_time_ms=elapsed_ms,
            error=content if content.startswith("[ERROR]") else None,
        )

        self._history.append(user_turn)
        self._history.append({"role": "assistant", "content": content})
        return result
# ratios: loc_comments=490:186 imports_exports=6:9 calls_definitions=125:26
