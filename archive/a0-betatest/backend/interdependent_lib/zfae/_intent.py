# ratios: loc_comments=38:52 imports_exports=3:2 calls_definitions=0:1
# === MODULE_BUILD ===
# id: zfae_intent_selector
#   module_name: _intent
#   module_kind: engine
#   summary: deterministic intent selector — maps (SemanticFeatures, ZFAE state) → one of a small fixed intent label set; pure function
#   owner: a0p maintainer
#   public_surface: select_intent, INTENT_LABELS, IntentLabel
#   internal_surface: none
#   auth_boundary: none
#   storage_boundary: none
#   network_boundary: none
#   user_data_boundary: none
#   admin_only: false
#   tests: a0p_skills.contracts.zfae_intent_dispatch_holds
#   rollout: default_enabled
#   rollback: revert file from git
# === END MODULE_BUILD ===
# === BOUNDARIES ===
# id: zfae_intent_selector_boundaries
#   summary: deterministic intent selector — maps (SemanticFeatures, ZFAE state) → one of a small fixed intent label set; pure function
#   auth_boundary: none
#   storage_boundary: none
#   network_boundary: none
#   user_data_boundary: none
#   admin_only: false
#   owner: a0p maintainer
# === END BOUNDARIES ===
# === CAPABILITIES ===
# id: zfae_intent_selector
#   summary: deterministic intent selector — maps (SemanticFeatures, ZFAE state) → one of a small fixed intent label set; pure function
#   exposes: select_intent, INTENT_LABELS, IntentLabel
#   boundaries: auth:none, storage:none, network:none, user_data:none
#   owner: a0p maintainer
# === END CAPABILITIES ===
# === CONTRACTS ===
# id: zfae_intent_dispatch
#   given: per the module's declared behaviour
#   then: the named callable returns without raising
#   class: correctness
#   call: a0p_skills.contracts.zfae_intent_dispatch_holds
# === END CONTRACTS ===
"""Intent selection for a0(zfae) — rule-based, deterministic."""
from __future__ import annotations
from typing import Literal
from ._parser import SemanticFeatures


IntentLabel = Literal[
    "acknowledge",
    "describe_state",
    "answer_question",
    "reflect_memory",
    "echo_with_analysis",
    "ask_clarification",
    "negation_received",
    "low_signal",
]

INTENT_LABELS: tuple[IntentLabel, ...] = (
    "acknowledge",
    "describe_state",
    "answer_question",
    "reflect_memory",
    "echo_with_analysis",
    "ask_clarification",
    "negation_received",
    "low_signal",
)


def select_intent(features: SemanticFeatures, coherence: float | None = None) -> IntentLabel:
    """Deterministic intent selection.

    Priority order is fixed:
      empty prompt        → low_signal
      negation present    → negation_received
      reflection + memory → reflect_memory
      question (?, qword) → answer_question if load>=0.2 else ask_clarification
      command head        → describe_state
      greeting            → acknowledge
      otherwise           → echo_with_analysis
    """
    if features.token_count == 0:
        return "low_signal"
    if features.negation and features.token_count < 6:
        return "negation_received"
    if features.reflection:
        return "reflect_memory"
    if features.question:
        return "answer_question" if features.semantic_load >= 0.2 else "ask_clarification"
    if features.command:
        return "describe_state"
    if features.greeting and features.token_count <= 4:
        return "acknowledge"
    return "echo_with_analysis"


__all__ = ["IntentLabel", "INTENT_LABELS", "select_intent"]
# ratios: loc_comments=38:52 imports_exports=3:2 calls_definitions=0:1
