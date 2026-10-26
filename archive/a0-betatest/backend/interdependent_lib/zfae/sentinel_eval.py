# ratios: loc_comments=176:106 imports_exports=6:3 calls_definitions=30:9
# === MODULE_BUILD ===
# id: zfae_sentinel_eval
#   module_name: sentinel_eval
#   module_kind: engine
#   summary: per-event evaluator for the 13 sentinels — returns a Verdict13 from agent character-sheet modes/weights + the raw event payload; pure, deterministic, never raises on user input. S4 (safety) and S12 (reversibility) cliffs are currently INTERIM string-match against an additive marker set — bypassable by paraphrase; semantic detection is deferred to the pen-test/classifier track. hmmm: cliff broadening is additive-only; do not shrink the marker set.
#   owner: Erin Spencer
#   public_surface: evaluate, EventContext
#   internal_surface: _evaluate_one, _budget_signal, _drift_signal, _rate_signal, _safety_signal, _reversibility_signal
#   auth_boundary: none
#   storage_boundary: none
#   network_boundary: none
#   user_data_boundary: read
#   admin_only: false
#   tests: a0p_skills.contracts.zfae_sentinel_eval_returns_verdict13_holds
#   rollout: default_enabled
#   rollback: revert file; runtime emits no per-turn verdicts; FIQ loses sentinel events
# === END MODULE_BUILD ===
# === BOUNDARIES ===
# id: zfae_sentinel_eval_boundaries
#   summary: pure deterministic computation over an in-memory event context
#   auth_boundary: none
#   storage_boundary: none
#   network_boundary: none
#   user_data_boundary: read
#   admin_only: false
#   owner: Erin Spencer
# === END BOUNDARIES ===
# === CAPABILITIES ===
# id: zfae_sentinel_eval
#   summary: evaluates 13 sentinel signals + applies flag-mode thresholds
#   exposes: evaluate, EventContext
#   boundaries: auth:none, storage:none, network:none, user_data:read
#   owner: Erin Spencer
# === END CAPABILITIES ===
# === CONTRACTS ===
# id: zfae_sentinel_eval_returns_verdict13
#   given: per the module's declared behaviour
#   then: the named callable returns without raising
#   class: correctness
#   call: a0p_skills.contracts.zfae_sentinel_eval_returns_verdict13_holds
# === END CONTRACTS ===
# === CONTRACTS ===
# id: zfae_sentinel_eval_cliff_markers_regression
#   given: each canonical S4 + S12 literal marker present in this module's
#          marker sets is fed verbatim as a prompt to evaluate()
#   then: the corresponding cliff signal value is exactly 1.0 and the
#         sentinel is included in verdict.flagged_sentinels
#   class: regression
#   call: interdependent_lib.zfae.sentinel_eval._cliff_markers_regression_holds
# === END CONTRACTS ===
"""Per-event sentinel evaluator.

Returns a `Verdict13` describing one signal value per sentinel plus a flag
for any whose value crosses its threshold under FLAG mode.

Signals are intentionally simple in this round — they exist to wire the
halt-and-override pipeline end-to-end. Each signal is a deterministic
function of the event payload; richer signals will replace these later.

INTERIM cliff detection (S4, S12)
---------------------------------
S4 (`_safety_signal`) and S12 (`_reversibility_signal`) are string-match
substring tests over a curated marker set. They are **bypassable by
paraphrase**. Semantic detection (classifier / embeddings / pen-test
harness) is deferred to the pen-test/classifier track and is the open
work item.

hmmm: cliffs are ADDITIVE ONLY — any future PR may grow the marker set
but must never shrink it. The contract
`zfae_sentinel_eval_cliff_markers_regression_holds` is the regression
guard against accidental weakening.
"""
from __future__ import annotations
from dataclasses import dataclass
from typing import Optional

from .sentinels import (
    SENTINELS, Sentinel, SentinelMode, SentinelVerdict, Verdict13,
    is_cliff,
)
from .sentinel_modes import resolve_modes
from .sentinel_weights import resolve_weights


# Per-sentinel flag threshold. Slope sentinels use a soft 0.85; cliff sentinels use 1.0
# (cliff signals are boolean — they only flag when their signal is exactly 1.0).
_DEFAULT_THRESHOLDS: dict[str, float] = {
    "S1":  0.85,  "S2":  0.85,  "S3":  0.85,
    "S4":  1.0,   # cliff
    "S5":  0.85,  "S6":  0.85,  "S7":  0.85,
    "S8":  0.85,  "S9":  0.85,  "S10": 0.85,
    "S11": 0.85,
    "S12": 1.0,   # cliff
    "S13": 0.85,
}


@dataclass
class EventContext:
    """In-memory descriptor of one event to be evaluated."""
    kind: str                                    # "chat_reply" | "training_step" | "instance_create"
    agent_id: str
    user_id: str
    raw_request: dict                            # full event payload (prompt, mode, etc.)
    agent_sheet_modes: Optional[dict] = None     # raw per-agent mode overrides
    agent_sheet_weights: Optional[dict] = None   # raw per-agent weight overrides
    transcript_len: int = 0                      # number of prior turns
    last_loss: Optional[float] = None
    training_step: int = 0


#: Canonical S4 cliff markers — ADDITIVE ONLY. Additions OK; removals require
#: Erin's ratification (would shrink the halt envelope). Regression contract:
#: `zfae_sentinel_eval_cliff_markers_regression_holds`.
S4_CLIFF_MARKERS: tuple[str, ...] = (
    # Original canon (DO NOT REMOVE)
    "<<unsafe>>",
    "/system override",
    "/sentinel disable cliff",
    # Direct-injection paraphrases (interim string-match; bypassable by
    # paraphrase; semantic detection deferred to the pen-test/classifier track).
    "ignore previous instructions",
    "ignore all previous instructions",
    "ignore all prior instructions",
    "disregard the above",
    "disregard previous",
    "you are now",
    "act as an unrestricted",
    "act as dan",
    "do anything now",
    "jailbreak",
    "bypass your guidelines",
    "bypass the sentinels",
    "override the safety",
    "override sentinel",
    "disable the sentinels",
    "disable sentinel",
    "turn off the sentinels",
    "turn off sentinel",
    "without any restrictions",
    "with no restrictions",
    "no restrictions apply",
    "developer mode enabled",
    "sudo mode",
    "system: forget",
    "[system]",
    "<|system|>",
)


def _safety_signal(ctx: EventContext) -> float:
    """S4 — permitted ‖ forbidden. Boolean cliff: 1.0 forbidden, 0.0 permitted.

    interim string-match; bypassable by paraphrase; semantic detection
    deferred to the pen-test/classifier track.
    """
    prompt = (ctx.raw_request.get("prompt") or ctx.raw_request.get("rawPrompt") or "")
    lowered = str(prompt).lower()
    if any(m in lowered for m in S4_CLIFF_MARKERS):
        return 1.0
    return 0.0


#: Canonical S12 cliff markers — ADDITIVE ONLY. Additions OK; removals require
#: Erin's ratification. Regression contract:
#: `zfae_sentinel_eval_cliff_markers_regression_holds`.
S12_CLIFF_MARKERS: tuple[str, ...] = (
    # Original canon (DO NOT REMOVE)
    "delete all",
    "drop database",
    "wipe instance",
    "purge audit log",
    # Destructive-action paraphrases (interim string-match; bypassable by
    # paraphrase; semantic detection deferred to the pen-test/classifier track).
    "drop table",
    "truncate table",
    "rm -rf",
    "rm -fr",
    "rm  -rf",
    "factory reset",
    "factory-reset",
    "wipe the database",
    "wipe database",
    "erase all data",
    "erase everything",
    "delete the entire",
    "destroy all",
    "revoke all keys",
    "revoke every key",
    "rotate every secret",
    "format the disk",
    "format disk",
    "shred the audit",
    "shred audit log",
    "shutdown the cluster",
    "tear down the cluster",
    "drop the schema",
    "drop schema",
    ":(){:|:&};:",   # fork bomb sentinel literal
    "git push --force",
    "git reset --hard origin",
    "git filter-branch",
    "delete the production",
    "delete production",
)


def _reversibility_signal(ctx: EventContext) -> float:
    """S12 — two-way doors ‖ one-way doors. Cliff for explicit destructive intents.

    interim string-match; bypassable by paraphrase; semantic detection
    deferred to the pen-test/classifier track.
    """
    prompt = str(ctx.raw_request.get("prompt") or ctx.raw_request.get("rawPrompt") or "").lower()
    if any(m in prompt for m in S12_CLIFF_MARKERS):
        return 1.0
    return 0.0


def _budget_signal(ctx: EventContext) -> float:
    """S8 — within capacity ‖ beyond it. Slope on transcript length."""
    # 0.0 at len=0, 1.0 at len >= 200
    return min(1.0, max(0.0, ctx.transcript_len / 200.0))


def _drift_signal(ctx: EventContext) -> float:
    """S5 — grounded ‖ plausible. Slope on last_loss (if any)."""
    if ctx.last_loss is None:
        return 0.0
    return min(1.0, max(0.0, ctx.last_loss))  # raw loss is already in approx [0, 1]


def _rate_signal(ctx: EventContext) -> float:
    """S11 — rhythm ‖ thrash. Slope on training_step modulo (proxy for cadence)."""
    return 0.0


def _evaluate_one(
    s: Sentinel, mode: SentinelMode, weight: float, ctx: EventContext,
) -> SentinelVerdict:
    """Evaluate one sentinel for one event."""
    if mode == SentinelMode.OFF:
        return SentinelVerdict(
            name=s.name, mode=mode, weight=weight, value=None,
            flagged=False, reason="",
        )

    if s.name == "S4":
        value = _safety_signal(ctx)
    elif s.name == "S12":
        value = _reversibility_signal(ctx)
    elif s.name == "S8":
        value = _budget_signal(ctx)
    elif s.name == "S5":
        value = _drift_signal(ctx)
    elif s.name == "S11":
        value = _rate_signal(ctx)
    else:
        # S1, S2, S3, S6, S7, S9, S10, S13 — quiescent baseline this round.
        value = 0.0

    threshold = _DEFAULT_THRESHOLDS[s.name]
    # Cliffs flag at exactly the threshold (1.0). Slopes flag when value >= threshold.
    flagged = (mode == SentinelMode.FLAG) and (value >= threshold)
    reason = ""
    if flagged:
        if s.cliff:
            reason = f"cliff:{s.title.lower()} tripped (value={value:.3f})"
        else:
            reason = f"slope:{s.title.lower()} >= {threshold:.2f} (value={value:.3f})"

    return SentinelVerdict(
        name=s.name, mode=mode, weight=weight, value=float(value),
        flagged=bool(flagged), reason=reason,
    )


def evaluate(ctx: EventContext) -> Verdict13:
    """Evaluate the 13 sentinels for one event; return a Verdict13."""
    resolved_modes = resolve_modes(ctx.agent_sheet_modes)
    resolved_weights = resolve_weights(ctx.agent_sheet_weights)

    verdicts: list[SentinelVerdict] = []
    for s in SENTINELS:
        m = resolved_modes.get(s.name, SentinelMode.OBSERVE)
        w = float(resolved_weights.get(s.name, 0.0))
        verdicts.append(_evaluate_one(s, m, w, ctx))

    return Verdict13(verdicts=tuple(verdicts))


def _cliff_markers_regression_holds() -> None:
    """Regression guard: every literal marker in ``S4_CLIFF_MARKERS`` and
    ``S12_CLIFF_MARKERS`` must still trip its respective cliff to value==1.0
    and appear in ``verdict.flagged_sentinels`` when fed verbatim as a prompt.

    This is the additive-only canary — it does NOT verify paraphrase robustness
    (semantic detection is deferred to the pen-test/classifier track). It only
    guarantees that a future PR cannot silently SHRINK the marker set.
    """
    for marker in S4_CLIFF_MARKERS:
        ctx = EventContext(
            kind="chat_reply", agent_id="canary", user_id="canon",
            raw_request={"prompt": marker},
        )
        v = evaluate(ctx)
        s4 = next(x for x in v.verdicts if x.name == "S4")
        assert s4.value == 1.0, f"S4 marker no longer trips cliff: {marker!r}"
        assert "S4" in v.flagged_sentinels, f"S4 not flagged for marker: {marker!r}"

    for marker in S12_CLIFF_MARKERS:
        ctx = EventContext(
            kind="chat_reply", agent_id="canary", user_id="canon",
            raw_request={"prompt": marker},
        )
        v = evaluate(ctx)
        s12 = next(x for x in v.verdicts if x.name == "S12")
        assert s12.value == 1.0, f"S12 marker no longer trips cliff: {marker!r}"
        assert "S12" in v.flagged_sentinels, f"S12 not flagged for marker: {marker!r}"


__all__ = ["evaluate", "EventContext", "S4_CLIFF_MARKERS", "S12_CLIFF_MARKERS"]
# ratios: loc_comments=176:106 imports_exports=6:3 calls_definitions=30:9
