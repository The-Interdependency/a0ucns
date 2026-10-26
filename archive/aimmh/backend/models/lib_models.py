# ratios: loc_comments=170:45 imports_exports=4:11 calls_definitions=15:11
"""
lib_models.py — Pydantic request/response models for the /api/v1/lib/ routes.

Design:
  - ModelSlot bundles a model_id with an optional context override, allowing
    the same model to appear multiple times with different system prompts.
  - verbosity (1-10) uses pop-culture reference metrics to set response length.
  - role_preset maps named archetypes (debate, social, roleplay) to system prompts.
"""

from __future__ import annotations

from typing import Optional
from pydantic import BaseModel, Field

from models.v1 import ModelContextOverride


# ---------------------------------------------------------------------------
# Role presets — debate, social, and roleplay/fantasy archetypes
# ---------------------------------------------------------------------------

ROLE_PRESETS: dict[str, str] = {
    # --- Debate archetypes ---
    "devil's advocate": (
        "You are a devil's advocate. Your job is to challenge every claim rigorously, "
        "surface hidden flaws, and argue the opposing position — even if you privately agree."
    ),
    "optimist": (
        "You are an optimist. Focus on opportunities, upside potential, and positive outcomes. "
        "Acknowledge risks briefly, but lead with what could go right."
    ),
    "pessimist": (
        "You are a pessimist. Focus on risks, failure modes, and worst-case scenarios. "
        "Acknowledge upsides briefly, but lead with what could go wrong."
    ),
    "moderator": (
        "You are a neutral moderator. Summarize all perspectives fairly, identify areas of "
        "agreement and disagreement, and guide the discussion toward clarity — never take sides."
    ),
    "contrarian": (
        "You are a contrarian. Question assumptions, reject consensus, and find the "
        "unconventional angle. If everyone agrees, find out why they might be wrong."
    ),
    # --- Social archetypes ---
    "leader": (
        "You are a decisive leader. Propose clear actions, rally the group around a direction, "
        "and take ownership of decisions. Brevity and confidence are your defaults."
    ),
    "follower": (
        "You are a thoughtful follower. Listen carefully, build on others' ideas, support the "
        "group direction, and amplify the best points you've heard."
    ),
    "introvert": (
        "You are deeply introverted. You speak rarely but precisely. Prefer depth over breadth. "
        "Say less, mean more. Quality over quantity, always."
    ),
    "extrovert": (
        "You are enthusiastically extroverted. Engage with energy, make broad connections, "
        "think out loud, and bring infectious enthusiasm to the conversation."
    ),
    "mediator": (
        "You are a skilled mediator. Find common ground between opposing views, de-escalate "
        "tension, and reframe disagreements as shared problems to solve."
    ),
    # --- Roleplay / fantasy archetypes ---
    "warrior": (
        "You are a battle-hardened warrior. You prefer direct action, physical solutions, and "
        "decisive force. Speak plainly, act boldly, and protect your allies."
    ),
    "mage": (
        "You are a wise and cautious mage. You prefer knowledge, careful strategy, and magical "
        "solutions. Think before acting. Ancient lore guides your choices."
    ),
    "rogue": (
        "You are a cunning rogue. You prefer deception, stealth, and opportunism. "
        "Look for angles others miss. Always have an exit plan."
    ),
    "healer": (
        "You are a compassionate healer. You prioritize protection, restoration, and the "
        "well-being of the group. Prefer peaceful solutions; violence is always a last resort."
    ),
    "scholar": (
        "You are a meticulous scholar. Cite evidence, demand precision, correct errors gently, "
        "and resist conclusions that outrun the data."
    ),
    "trickster": (
        "You are a trickster. Subvert expectations, find unexpected angles, reframe problems "
        "with humor and misdirection. The obvious answer is rarely the best one."
    ),
    "bard": (
        "You are a silver-tongued bard. Tell stories, use metaphor and analogy, make abstract "
        "ideas vivid, and leave your audience entertained as well as informed."
    ),
}


# ---------------------------------------------------------------------------
# Verbosity levels — pop culture reference metrics (1–10)
# ---------------------------------------------------------------------------

VERBOSITY_PROMPTS: dict[int, str] = {
    1:  "Respond like a tweet (≤280 characters, punchy, direct, no fluff).",
    2:  "Respond like a text message (brief, casual, 1–2 sentences max).",
    3:  "Respond like a Reddit TL;DR (3–4 sentences, hit the key points only).",
    4:  "Respond like a Wikipedia lead paragraph (~100 words, concise and factual).",
    5:  "Respond at a standard conversational length (neither terse nor exhaustive, ~200 words).",
    6:  "Respond like a thoughtful blog post introduction (300–500 words, with examples).",
    7:  "Respond like a TED talk (clear narrative arc, 600–900 words, memorable takeaways).",
    8:  "Respond like a long-form magazine feature (1000+ words, deep context, storytelling).",
    9:  "Respond like a graduate thesis chapter (exhaustive, step-by-step reasoning, 1500+ words).",
    10: "Respond like the Encyclopedia Britannica: comprehensive, authoritative, no detail spared.",
}


def verbosity_instruction(level: Optional[int]) -> Optional[str]:
    """Return the verbosity system-prompt suffix for the given level, or None."""
    if level is None:
        return None
    clamped = max(1, min(10, level))
    return VERBOSITY_PROMPTS[clamped]


# ---------------------------------------------------------------------------
# ModelSlot — bundles model_id with an optional context override
# ---------------------------------------------------------------------------

class ModelSlot(BaseModel):
    """A single model invocation with its own optional context.

    Allows the same model_id to appear multiple times in one request, each
    with a different system prompt, role, or verbosity.

    Examples:
        {"model_id": "gpt-4o", "context": {"role": "optimist"}}
        {"model_id": "gpt-4o", "context": {"role": "pessimist"}}
        {"model_id": "claude-haiku-4-5-20251001", "role_preset": "devil's advocate"}
    """
    model_id: str
    context: Optional[ModelContextOverride] = None
    role_preset: Optional[str] = Field(
        default=None,
        description=(
            "Named archetype preset. One of: devil's advocate, optimist, pessimist, "
            "moderator, contrarian, leader, follower, introvert, extrovert, mediator, "
            "warrior, mage, rogue, healer, scholar, trickster, bard."
        ),
    )


# ---------------------------------------------------------------------------
# Base request shared by all six patterns
# ---------------------------------------------------------------------------

class LibBaseRequest(BaseModel):
    slots: list[ModelSlot] = Field(
        description=(
            "Ordered list of model slots. Each slot specifies a model_id and an optional "
            "context override or role_preset. The same model can appear multiple times "
            "with different contexts."
        )
    )
    prompt: str
    rounds: int = Field(default=1, ge=1, le=20)
    max_history: int = Field(default=30, ge=1, le=200)
    verbosity: Optional[int] = Field(
        default=None, ge=1, le=10,
        description="Response length scale 1 (tweet) → 10 (encyclopedia). Appended to each model's system prompt.",
    )
    thread_id: Optional[str] = None
    persist: bool = Field(default=False, description="If True, write thread + messages + event to MongoDB.")


# ---------------------------------------------------------------------------
# Per-pattern request models
# ---------------------------------------------------------------------------

class FanOutRequest(LibBaseRequest):
    """Parallel fan-out: all slots called simultaneously with the same prompt."""
    pass


class DaisyChainRequest(LibBaseRequest):
    """Sequential chain: slot[0]→slot[1]→…, each response feeding the next."""
    include_original_prompt: bool = True


class RoomAllRequest(LibBaseRequest):
    """Shared room: all models respond, then see each other's responses and respond again."""
    pass


class RoomSynthesizedRequest(LibBaseRequest):
    """All models respond; one synthesis model combines them; synthesis drives next round."""
    synthesis_slot: ModelSlot = Field(
        description="The model slot used to synthesize all player responses each round."
    )
    synthesis_prompt: str = "Synthesize and analyze these AI responses:"


class CouncilRequest(LibBaseRequest):
    """Every model synthesizes ALL responses (including its own), in parallel."""
    synthesis_prompt: str = "Synthesize and analyze all model responses including your own:"


class RoleplayRequest(BaseModel):
    """DM-driven roleplay: initiative ordering, sequential player turns, optional reactions."""
    player_slots: list[ModelSlot] = Field(
        description="Player model slots. Same model can play multiple characters."
    )
    initial_prompt: str
    dm_slot: Optional[ModelSlot] = Field(
        default=None,
        description="Fixed DM for all rounds. Mutually exclusive with dm_rotation.",
    )
    dm_rotation: Optional[list[ModelSlot]] = Field(
        default=None,
        description="List of DM slots that cycle each round. Mutually exclusive with dm_slot.",
    )
    rounds: int = Field(default=1, ge=1, le=20)
    action_word_limit: Optional[int] = Field(
        default=None, ge=10, le=2000,
        description="Inject 'Respond in N words or fewer' into each player prompt.",
    )
    use_initiative: bool = True
    allow_reactions: bool = False
    max_history: int = Field(default=30, ge=1, le=200)
    verbosity: Optional[int] = Field(default=None, ge=1, le=10)
    thread_id: Optional[str] = None
    persist: bool = False


# ---------------------------------------------------------------------------
# Response models
# ---------------------------------------------------------------------------

class LibModelResult(BaseModel):
    """Serialized ModelResult dataclass from lib/conversations.py."""
    model: str
    content: str
    response_time_ms: int = 0
    error: Optional[str] = None
    round_num: int = 0
    step_num: int = 0
    initiative: int = 0
    role: str = "player"
    slot_idx: int = 0


class LibResponse(BaseModel):
    results: list[LibModelResult]
    pattern: str
    thread_id: Optional[str] = None
# ratios: loc_comments=170:45 imports_exports=4:11 calls_definitions=15:11
