# ratios: loc_comments=179:48 imports_exports=4:6 calls_definitions=60:8
# === MODULE_BUILD ===
# id: carrier_gonal
#   module_name: gonal
#   module_kind: engine
#   summary: builds and validates a gonal character carrier arrangement from a declarative spec (user-provided canonical module)
#   owner: Erin Spencer
#   public_surface: GonalSpec, build_gonal, validate_gonal, print_gonal, EXAMPLE_157, make_example_157
#   internal_surface: UPPERCASE, LOWERCASE, DIGITS_ODD, DIGITS_EVEN, PAIRED_OPEN, PAIRED_CLOSE, UNPAIRED_ASCII, UNPAIRED_OPS, UNPAIRED_ALL
#   auth_boundary: none
#   storage_boundary: none
#   network_boundary: none
#   user_data_boundary: none
#   admin_only: false
#   tests: a0p_skills.contracts.gonal_example_157_holds
#   rollout: usable; EXAMPLE_157 is a public non-secret arrangement for testing only
#   rollback: revert to placeholder fixture; arrangements built from this module are not secret
# === END MODULE_BUILD ===
# === BOUNDARIES ===
# id: carrier_gonal_boundaries
#   summary: pure construction; no IO; EXAMPLE_157 is public
#   auth_boundary: none
#   storage_boundary: none
#   network_boundary: none
#   user_data_boundary: none
#   admin_only: false
#   owner: Erin Spencer
# === END BOUNDARIES ===
# === CAPABILITIES ===
# id: carrier_gonal
#   summary: builds and validates a gonal character carrier arrangement from a declarative spec
#   exposes: GonalSpec, build_gonal, validate_gonal, print_gonal, EXAMPLE_157
#   boundaries: auth:none, storage:none, network:none, user_data:none
#   owner: Erin Spencer
# === END CAPABILITIES ===
"""
gonal.py — build a gonal arrangement from spec options. User-canonical module.

A gonal is a circular carrier of n positions (n prime, consciousness prime
recommended) where each position holds one character. The arrangement is
governed by adjacency constraints and placement rules.
"""
from __future__ import annotations
import string
from dataclasses import dataclass, field
from typing import Optional

UPPERCASE = list(string.ascii_uppercase)
LOWERCASE = list(string.ascii_lowercase)
DIGITS_ODD  = ['1', '3', '5', '7', '9']
DIGITS_EVEN = ['2', '4', '6', '8', '0']
DIGITS_ALL  = DIGITS_ODD + DIGITS_EVEN

PAIRED_OPEN  = ['(', '[', '{', '<', '\u2018', '\u201C', '\u00AB']
PAIRED_CLOSE = [')', ']', '}', '>', '\u2019', '\u201D', '\u00BB']

UNPAIRED_ASCII = [
    chr(i) for i in range(33, 127)
    if chr(i) not in (
        set(UPPERCASE) | set(LOWERCASE) | set(string.digits) |
        set(PAIRED_OPEN) | set(PAIRED_CLOSE) | {' '}
    )
]

UNPAIRED_OPS = [
    '…', '—', '–', '·', '°', '±', '×', '÷', '√',
    '∂', '∫', '∑', '∏', '∇', '∞', '≈', '≠', '≤', '≥',
    '→', '←', '↑', '↓', '↔', '⊕', '⊗', '⊙', '⊘',
    '∈', '∉', '⊂', '⊃', '⊆', '⊇', '∩', '∪',
    '∧', '∨', '¬', '∀', '∃', '⊢', '⊨', '∴', '∵', '≡',
    'ψ', 'φ', 'ω', 'α', 'β', 'γ', 'δ', 'λ', 'π', 'σ', 'τ', 'θ',
    '∅', 'ℕ', 'ℤ', 'ℚ', 'ℝ', 'ℂ', 'ℵ',
]

UNPAIRED_ALL = UNPAIRED_ASCII + UNPAIRED_OPS


@dataclass
class GonalSpec:
    n: int = 157
    no_adjacent: list[str] = field(default_factory=lambda: ['letter', 'digit'])
    letter_sides: str = 'opposite'
    digit_alternation: bool = True
    paired_alignment: str = 'opposite'
    horizontal_symmetry: str = 'forbidden'
    origin: str = ' '
    extra_unpaired: list[str] = field(default_factory=list)
    seed: Optional[int] = None


def build_gonal(spec: GonalSpec) -> list[str]:
    n = spec.n
    slot: list[str] = [''] * n
    slot[0] = spec.origin

    upper_arc = list(range(1, (n // 2) + 1))
    lower_arc = list(range((n // 2) + 1, n))

    if spec.letter_sides == 'opposite':
        upper_L = list(range(1, upper_arc[-1], 3))[:26]
        lower_L = list(range(lower_arc[1], lower_arc[-1], 3))[:26]
        for i, ch in enumerate(UPPERCASE):
            slot[upper_L[i]] = ch
        for i, ch in enumerate(LOWERCASE):
            slot[lower_L[i]] = ch
    elif spec.letter_sides == 'same':
        all_letters: list[Optional[str]] = [None] * 52
        all_letters[::2]  = UPPERCASE
        all_letters[1::2] = LOWERCASE
        upper_L = list(range(1, upper_arc[-1], 2))[:52]
        for i, ch in enumerate(all_letters):
            if i < len(upper_L) and ch is not None:
                slot[upper_L[i]] = ch

    if spec.digit_alternation:
        upper_gaps = [p for p in upper_arc if slot[p] == '']
        step = max(1, len(upper_gaps) // (len(DIGITS_ODD) + 1))
        for i, ch in enumerate(DIGITS_ODD):
            idx = step * (i + 1)
            if idx < len(upper_gaps):
                slot[upper_gaps[idx]] = ch

        lower_gaps = [p for p in lower_arc if slot[p] == '']
        step_l = max(1, len(lower_gaps) // (len(DIGITS_EVEN) + 1))
        for i, ch in enumerate(DIGITS_EVEN):
            idx = step_l * (i + 1)
            if idx < len(lower_gaps):
                slot[lower_gaps[idx]] = ch
    else:
        all_gaps = [p for p in range(1, n) if slot[p] == '']
        step = max(1, len(all_gaps) // (len(DIGITS_ALL) + 1))
        for i, ch in enumerate(DIGITS_ALL):
            idx = step * (i + 1)
            if idx < len(all_gaps):
                slot[all_gaps[idx]] = ch

    if spec.paired_alignment == 'opposite':
        upper_rem = [p for p in upper_arc if slot[p] == '']
        lower_rem = [p for p in lower_arc if slot[p] == '']
        step_o = max(1, len(upper_rem) // (len(PAIRED_OPEN) + 1))
        step_c = max(1, len(lower_rem) // (len(PAIRED_CLOSE) + 1))
        for i, ch in enumerate(PAIRED_OPEN):
            idx = step_o * (i + 1)
            if idx < len(upper_rem):
                slot[upper_rem[idx]] = ch
        for i, ch in enumerate(PAIRED_CLOSE):
            idx = step_c * (i + 1)
            if idx < len(lower_rem):
                slot[lower_rem[idx]] = ch
    elif spec.paired_alignment == 'interleaved':
        all_rem = [p for p in range(1, n) if slot[p] == '']
        step_p = max(1, len(all_rem) // (len(PAIRED_OPEN) + 1))
        for i, (op, cl) in enumerate(zip(PAIRED_OPEN, PAIRED_CLOSE)):
            idx = step_p * (i + 1)
            if idx < len(all_rem):
                pos = all_rem[idx]
                slot[pos] = op
                nxt = (pos + 1) % n
                if slot[nxt] == '':
                    slot[nxt] = cl

    unpaired = UNPAIRED_ALL + spec.extra_unpaired
    fill_positions = [p for p in range(n) if slot[p] == '']
    for i, pos in enumerate(fill_positions):
        if i < len(unpaired):
            slot[pos] = unpaired[i]
        else:
            slot[pos] = f'\x00{i}'

    return slot


def validate_gonal(slot: list[str], spec: GonalSpec) -> dict:
    n = len(slot)
    violations = []
    warnings = []

    def char_type(ch: str) -> str:
        if ch in UPPERCASE: return 'uppercase'
        if ch in LOWERCASE: return 'lowercase'
        if ch in string.digits: return 'digit'
        if ch in PAIRED_OPEN: return 'paired_open'
        if ch in PAIRED_CLOSE: return 'paired_close'
        if ch == spec.origin: return 'origin'
        return 'unpaired'

    def is_letter(ch): return ch in string.ascii_letters
    def is_digit(ch): return ch in string.digits

    for k in range(n):
        curr = slot[k]
        nxt = slot[(k + 1) % n]
        for constraint in spec.no_adjacent:
            if constraint == 'letter':
                if is_letter(curr) and is_letter(nxt):
                    violations.append(f"letter-letter at pos {k}-{(k+1)%n}: {curr!r}-{nxt!r}")
            elif constraint == 'digit':
                if is_digit(curr) and is_digit(nxt):
                    violations.append(f"digit-digit at pos {k}-{(k+1)%n}: {curr!r}-{nxt!r}")
            elif constraint == 'uppercase':
                if curr in UPPERCASE and nxt in UPPERCASE:
                    violations.append(f"upper-upper at pos {k}-{(k+1)%n}: {curr!r}-{nxt!r}")
            elif constraint == 'lowercase':
                if curr in LOWERCASE and nxt in LOWERCASE:
                    violations.append(f"lower-lower at pos {k}-{(k+1)%n}: {curr!r}-{nxt!r}")

    overflow = [k for k in range(n) if str(slot[k]).startswith('\x00')]
    if overflow:
        violations.append(f"overflow positions (ran out of unpaired chars): {overflow}")

    return {
        'valid': len(violations) == 0,
        'violations': violations,
        'warnings': warnings,
        'counts': {t: sum(1 for s in slot if char_type(s) == t) for t in
                   ['uppercase', 'lowercase', 'digit', 'paired_open', 'paired_close', 'unpaired', 'origin']},
        'n': n,
    }


def print_gonal(slot: list[str], width: int = 10) -> None:
    n = len(slot)
    print(f"\n{n}-GONAL ARRANGEMENT")
    print(f"  pos   0: {slot[0]!r}  ORIGIN")
    for i in range(0, n, width):
        end = min(i + width, n)
        row = '  '.join(f"{j:3}:{slot[j]!r}" for j in range(i, end))
        print(f"  {row}")


def make_example_157() -> list[str]:
    """Public non-secret 157-gonal arrangement for testing only."""
    spec = GonalSpec(
        n=157,
        no_adjacent=['letter', 'digit'],
        letter_sides='opposite',
        digit_alternation=True,
        paired_alignment='opposite',
        horizontal_symmetry='forbidden',
        origin=' ',
    )
    return build_gonal(spec)


EXAMPLE_157: list[str] = make_example_157()


__all__ = [
    "GonalSpec", "build_gonal", "validate_gonal", "print_gonal",
    "EXAMPLE_157", "make_example_157",
    "UPPERCASE", "LOWERCASE", "DIGITS_ODD", "DIGITS_EVEN",
    "PAIRED_OPEN", "PAIRED_CLOSE", "UNPAIRED_ALL",
]


# === CONTRACTS ===
# id: carrier_gonal_loads
#   given: module declares its msdmd canon
#   then: the module imports cleanly under the current interpreter
#   class: integration
#   call: a0p_skills.contracts.module_imports_cleanly_holds
# === END CONTRACTS ===
# ratios: loc_comments=179:48 imports_exports=4:6 calls_definitions=60:8
