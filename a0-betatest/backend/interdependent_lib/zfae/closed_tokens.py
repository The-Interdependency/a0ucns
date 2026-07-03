# ratios: loc_comments=73:69 imports_exports=1:5 calls_definitions=17:4
# === MODULE_BUILD ===
# id: zfae_closed_tokens
#   module_name: closed_tokens
#   module_kind: schema
#   summary: morphological bone inventory — the closed-class word set + bound-morpheme (affix) set the BoneGonal (omega) sources its structural vertices from; the open-class test is the complement used by the RootGonal (phi)
#   owner: Erin Spencer
#   public_surface: CLOSED_CLASS, AFFIXES, is_closed_class, is_affix, is_open_class, strip_affixes
#   internal_surface: _PREFIXES, _SUFFIXES
#   auth_boundary: none
#   storage_boundary: none
#   network_boundary: none
#   user_data_boundary: read
#   admin_only: false
#   tests: a0p_skills.contracts.zfae_closed_tokens_partition_holds
#   rollout: default_enabled
#   rollback: revert file from git
#   hmmm: the seed inventories below are an initial English bone/affix set — load-bearing as the structural (omega) vocabulary, owner-extendable; not exhaustive
# === END MODULE_BUILD ===
# === BOUNDARIES ===
# id: zfae_closed_tokens_boundaries
#   summary: pure data + predicates over morphological token classes; no IO, no globals, no LLM
#   auth_boundary: none
#   storage_boundary: none
#   network_boundary: none
#   user_data_boundary: read
#   admin_only: false
#   owner: Erin Spencer
# === END BOUNDARIES ===
# === CAPABILITIES ===
# id: zfae_closed_tokens
#   summary: closed-class + affix inventories and membership predicates for the morphological gonal stack
#   exposes: CLOSED_CLASS, AFFIXES, is_closed_class, is_affix, is_open_class
#   boundaries: auth:none, storage:none, network:none, user_data:read
#   owner: Erin Spencer
# === END CAPABILITIES ===
# === CONTRACTS ===
# id: zfae_closed_tokens_partition
#   given: per the module's declared behaviour
#   then: the named callable returns without raising
#   class: correctness
#   call: a0p_skills.contracts.zfae_closed_tokens_partition_holds
# === END CONTRACTS ===
"""Morphological bone inventory for the BoneGonal (omega).

The depth-ladder splits linguistic material by core:
  - omega (bones) — closed-class words + bound morphemes (affixes). Structural.
  - phi   (roots) — open-class stems. Content. (Defined here only by complement.)

Bones are the *operator / structural* layer: function words and the affixes
that inflect/derive open-class stems. They carry grammar, not content. This is
the vocabulary the BoneGonal inscribes from; the RootGonal inscribes from the
open-class complement.
"""
from __future__ import annotations


# Closed-class (function) words: determiners, pronouns, prepositions,
# conjunctions, auxiliaries, particles, complementizers, degree words.
CLOSED_CLASS: frozenset[str] = frozenset({
    # determiners / articles / quantifiers
    "a", "an", "the", "this", "that", "these", "those", "some", "any", "no",
    "every", "each", "all", "both", "few", "many", "much", "more", "most",
    "several", "such", "another", "either", "neither",
    # pronouns
    "i", "you", "he", "she", "it", "we", "they", "me", "him", "her", "us",
    "them", "my", "your", "his", "its", "our", "their", "mine", "yours",
    "hers", "ours", "theirs", "who", "whom", "whose", "which", "what",
    "myself", "yourself", "himself", "herself", "itself", "ourselves",
    "themselves", "one", "ones", "someone", "anyone", "everyone", "nobody",
    "something", "anything", "everything", "nothing",
    # prepositions
    "of", "in", "on", "at", "by", "for", "with", "about", "against",
    "between", "into", "through", "during", "before", "after", "above",
    "below", "to", "from", "up", "down", "over", "under", "again", "further",
    "then", "once", "off", "out", "near", "per", "via", "onto", "upon",
    "within", "without", "toward", "towards", "amongst", "among", "across",
    # conjunctions / complementizers
    "and", "but", "or", "nor", "so", "yet", "because", "as", "until",
    "while", "if", "though", "although", "unless", "whereas", "whether",
    "since", "than", "that",
    # auxiliaries / modals / copula
    "be", "am", "is", "are", "was", "were", "been", "being", "have", "has",
    "had", "do", "does", "did", "will", "would", "shall", "should", "can",
    "could", "may", "might", "must", "ought",
    # particles / degree / negation
    "not", "no", "only", "just", "very", "too", "also", "even", "still",
    "well", "there", "here", "now", "ever", "never",
})

# Bound morphemes — derivational + inflectional affixes the bones layer carries.
_PREFIXES: frozenset[str] = frozenset({
    "un", "re", "in", "im", "il", "ir", "dis", "en", "em", "non", "over",
    "mis", "sub", "pre", "inter", "fore", "de", "trans", "super", "semi",
    "anti", "mid", "under", "co", "auto", "bi", "tri", "mono", "multi",
})
_SUFFIXES: frozenset[str] = frozenset({
    "s", "es", "ed", "ing", "ly", "er", "or", " er", "est", "ment", "ness",
    "tion", "sion", "ity", "ous", "ive", "ize", "ise", "able", "ible", "al",
    "ful", "less", "ish", "ant", "ent", "ence", "ance", "ate", "en", "ic",
    "ism", "ist", "ship", "hood", "dom", "ward", "wise",
})
AFFIXES: frozenset[str] = _PREFIXES | _SUFFIXES


def is_closed_class(token: str) -> bool:
    """True iff the token is a closed-class (function) word — a bone."""
    return isinstance(token, str) and token.lower() in CLOSED_CLASS


def is_affix(token: str) -> bool:
    """True iff the token is a bound morpheme (prefix or suffix) — a bone."""
    return isinstance(token, str) and token.lower() in AFFIXES


def is_open_class(token: str) -> bool:
    """True iff the token is an open-class stem — a root (the phi complement).

    A token is a root when it is neither a closed-class word nor a bare affix.
    """
    if not isinstance(token, str) or not token.strip():
        return False
    t = token.lower()
    return t not in CLOSED_CLASS and t not in AFFIXES


def strip_affixes(token: str) -> str:
    """Peel known prefixes/suffixes off a token to expose its candidate root.

    Deterministic, longest-match-first; structural only — it does not consult
    a lexicon, so it is a morphological approximation of the root stem.
    """
    if not isinstance(token, str):
        return ""
    t = token.lower().strip()
    changed = True
    while changed and len(t) > 2:
        changed = False
        for p in sorted(_PREFIXES, key=len, reverse=True):
            if t.startswith(p) and len(t) - len(p) >= 2:
                t = t[len(p):]
                changed = True
                break
        for s in sorted((x for x in _SUFFIXES if x.strip()), key=len, reverse=True):
            s = s.strip()
            if t.endswith(s) and len(t) - len(s) >= 2:
                t = t[: len(t) - len(s)]
                changed = True
                break
    return t


__all__ = [
    "CLOSED_CLASS",
    "AFFIXES",
    "is_closed_class",
    "is_affix",
    "is_open_class",
    "strip_affixes",
]
# ratios: loc_comments=73:69 imports_exports=1:5 calls_definitions=17:4
