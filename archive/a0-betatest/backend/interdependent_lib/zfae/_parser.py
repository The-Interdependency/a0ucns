# ratios: loc_comments=77:45 imports_exports=3:3 calls_definitions=26:3
# === MODULE_BUILD ===
# id: zfae_semantic_parser
#   module_name: _parser
#   module_kind: engine
#   summary: deterministic prompt parser — token stats, intent surfaces (question, greeting, command, reflection), semantic load
#   owner: a0p maintainer
#   public_surface: parse_semantic, SemanticFeatures
#   internal_surface: _GREETING_TOKENS, _COMMAND_HEADS, _REFLECTION_WORDS, _NEGATION_WORDS
#   auth_boundary: none
#   storage_boundary: none
#   network_boundary: none
#   user_data_boundary: read
#   admin_only: false
#   tests: a0p_skills.contracts.zfae_parser_deterministic_holds
#   rollout: default_enabled
#   rollback: revert file from git
# === END MODULE_BUILD ===
# === BOUNDARIES ===
# id: zfae_semantic_parser_boundaries
#   summary: deterministic prompt parser — token stats, intent surfaces (question, greeting, command, reflection), semantic load
#   auth_boundary: none
#   storage_boundary: none
#   network_boundary: none
#   user_data_boundary: read
#   admin_only: false
#   owner: a0p maintainer
# === END BOUNDARIES ===
# === CAPABILITIES ===
# id: zfae_semantic_parser
#   summary: deterministic prompt parser — token stats, intent surfaces (question, greeting, command, reflection), semantic load
#   exposes: parse_semantic, SemanticFeatures
#   boundaries: auth:none, storage:none, network:none, user_data:read
#   owner: a0p maintainer
# === END CAPABILITIES ===
# === CONTRACTS ===
# id: zfae_parser_deterministic
#   given: per the module's declared behaviour
#   then: the named callable returns without raising
#   class: correctness
#   call: a0p_skills.contracts.zfae_parser_deterministic_holds
# === END CONTRACTS ===
"""Deterministic semantic parser for a0(zfae) — no NLP libraries, stdlib only."""
from __future__ import annotations
import re
from dataclasses import dataclass, field, asdict


_GREETING_TOKENS = frozenset({
    "hi", "hello", "hey", "greetings", "yo", "hola", "ack", "ping",
})

_COMMAND_HEADS = frozenset({
    "show", "tell", "describe", "list", "analyze", "compute", "summarize",
    "explain", "give", "produce", "report", "render", "run", "trace",
})

_REFLECTION_WORDS = frozenset({
    "remember", "recall", "history", "before", "previously", "earlier",
    "prior", "memory", "context", "log",
})

_NEGATION_WORDS = frozenset({
    "no", "not", "never", "none", "neither", "nor", "without",
})

_QUESTION_WORDS = frozenset({
    "what", "why", "how", "when", "where", "who", "which",
})

_WORD_RE = re.compile(r"[A-Za-z][A-Za-z0-9_'-]+")


@dataclass(frozen=True)
class SemanticFeatures:
    """A pure, JSON-friendly fingerprint of a raw prompt."""
    raw_length: int
    token_count: int
    tokens: tuple[str, ...]
    keywords: tuple[str, ...]
    question: bool
    greeting: bool
    command: bool
    reflection: bool
    negation: bool
    digit_count: int
    semantic_load: float    # 0..1 normalised heuristic
    first_word: str
    question_words: tuple[str, ...]

    def to_dict(self) -> dict:
        return asdict(self)


def parse_semantic(raw_prompt: str) -> SemanticFeatures:
    """Pure function — same input → same SemanticFeatures."""
    if raw_prompt is None:
        raw_prompt = ""
    text = str(raw_prompt)
    words = [m.group(0).lower() for m in _WORD_RE.finditer(text)]
    if not words:
        return SemanticFeatures(
            raw_length=len(text), token_count=0, tokens=(), keywords=(),
            question=False, greeting=False, command=False, reflection=False,
            negation=False, digit_count=sum(c.isdigit() for c in text),
            semantic_load=0.0, first_word="", question_words=(),
        )
    qwords = tuple(w for w in words if w in _QUESTION_WORDS)
    head = words[0]
    has_q_mark = "?" in text
    greeting = bool(set(words[:3]) & _GREETING_TOKENS)
    command = head in _COMMAND_HEADS
    reflection = bool(set(words) & _REFLECTION_WORDS)
    negation = bool(set(words) & _NEGATION_WORDS)
    question = has_q_mark or len(qwords) > 0
    digit_count = sum(c.isdigit() for c in text)
    keywords = tuple(dict.fromkeys(w for w in words if len(w) > 4))[:8]
    # semantic_load is a crude information-density proxy capped at 1.0
    load = min(1.0, (len(words) / 40.0) + (len(keywords) / 16.0))
    return SemanticFeatures(
        raw_length=len(text),
        token_count=len(words),
        tokens=tuple(words),
        keywords=keywords,
        question=question,
        greeting=greeting,
        command=command,
        reflection=reflection,
        negation=negation,
        digit_count=digit_count,
        semantic_load=round(load, 6),
        first_word=head,
        question_words=qwords,
    )


__all__ = ["SemanticFeatures", "parse_semantic"]
# ratios: loc_comments=77:45 imports_exports=3:3 calls_definitions=26:3
