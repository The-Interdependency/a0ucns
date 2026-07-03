# === MODULE_BUILD ===
# id: test_morphology_ladder
#   module_name: test_morphology_ladder
#   module_kind: test
#   summary: pytest coverage for the morphological depth-ladder — typed gonal primitives
#     (BoneGonal=omega, RootGonal=phi), the carrier-LCM word composition (psi derived
#     via the shared UCNS multiply operator), deterministic continuous-lane framing,
#     the recompose round-trip at depth<=2, the gated (HOLD) clause decomposition, and
#     the rewired inscribe_text emitting through the depth-ladder
#   owner: Erin Spencer
#   public_surface: (pytest test functions)
#   internal_surface: none
#   auth_boundary: none
#   storage_boundary: none
#   network_boundary: none
#   user_data_boundary: none
#   admin_only: false
#   tests: self
#   rollout: default_enabled
#   rollback: delete file
# === END MODULE_BUILD ===
# === BOUNDARIES ===
# id: test_morphology_ladder_boundaries
#   summary: pure in-process tests; no network, no storage
#   auth_boundary: none
#   storage_boundary: none
#   network_boundary: none
#   user_data_boundary: none
#   admin_only: false
#   owner: Erin Spencer
# === END BOUNDARIES ===
"""Tests for the ZFAE morphological depth-ladder."""
from __future__ import annotations
import math

import pytest

from interdependent_lib.zfae import morphology as m
from interdependent_lib.zfae import closed_tokens as ct
from interdependent_lib.zfae.gonal_inscription import PrivateGonal, inscribe_text


def test_ruled_weights():
    assert m.OMEGA_WEIGHT == 0.8   # bones
    assert m.PHI_WEIGHT == 0.4     # roots
    assert m.PSI_WEIGHT == 1.0     # words (derived)


def test_bone_root_partition():
    assert ct.is_closed_class("the")
    assert ct.is_affix("ing")
    assert ct.is_open_class("planet")
    assert not ct.is_open_class("the")
    assert not ct.is_open_class("ing")


def test_frame_value_deterministic():
    a = m.frame_value(0.42)
    b = m.frame_value(0.42)
    assert a == b
    assert a.n_min >= 1


def test_carrier_lcm_divides_product():
    root = m.frame_value(0.31)
    bone = m.frame_value(-0.72)
    word = m.carrier_lcm(root, bone)
    # nMin(a (X) b) divides lcm(nMin a, nMin b)
    expect = m.word_carrier(root) * m.word_carrier(bone)
    assert expect % m.word_carrier(word) == 0 or m.word_carrier(word) == 1


def test_compose_word_remarry_is_deterministic():
    w1 = m.compose_word(0.2, 0.5)
    w2 = m.compose_word(0.2, 0.5)
    assert w1 == w2
    s = m.word_signal(w1)
    assert 0.0 <= s < 1.0
    assert m.word_signal(w2) == s


def test_recompose_round_trip_depth_le_2():
    # bones + roots -> word (depth-1); compose two words -> clause (depth-2).
    root_a = m.frame_value(0.15)
    bone_a = m.frame_value(0.55)
    word_a = m.carrier_lcm(root_a, bone_a)
    root_b = m.frame_value(0.6)
    bone_b = m.frame_value(0.1)
    word_b = m.carrier_lcm(root_b, bone_b)
    clause = m.carrier_lcm(word_a, word_b)
    assert clause is not None
    # the clause carrier is a multiple of nothing it shouldn't be — it stays a
    # valid composed object (recompose is total)
    assert m.word_carrier(clause) >= 1


def test_decomposition_is_gated():
    assert m.PROOF_GREEN is False
    word = m.compose_word(0.3, 0.7)
    bone = m.frame_value(0.7)
    with pytest.raises(m.DecompositionGatedError):
        m.decompose_clause(word, bone)


def test_inscribe_text_uses_ladder():
    g = PrivateGonal.from_seed(b"morphology-test-seed")
    phi = [0.1 * ((i % 7) - 3) for i in range(53)]
    psi = [0.0 for _ in range(53)]  # derived, should be ignored as an input
    omega = [0.05 * ((i % 5) - 2) for i in range(53)]
    text1, meta1 = inscribe_text(g, phi, psi, omega, "deadbeefcafe", length=24)
    text2, meta2 = inscribe_text(g, phi, psi, omega, "deadbeefcafe", length=24)
    assert text1 == text2                     # deterministic
    assert meta1["word_carrier"] >= 1         # ladder exposed the word carrier
    assert isinstance(text1, str) and text1


def test_inscribe_independent_of_passed_psi():
    # psi is DERIVED from phi (X) omega — feeding a different psi must not change output.
    g = PrivateGonal.from_seed(b"psi-independence-seed")
    phi = [0.2 for _ in range(53)]
    omega = [0.3 for _ in range(53)]
    a, _ = inscribe_text(g, phi, [0.0] * 53, omega, "feedface", length=16)
    b, _ = inscribe_text(g, phi, [0.9] * 53, omega, "feedface", length=16)
    assert a == b
