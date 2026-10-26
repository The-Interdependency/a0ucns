# === MODULE_BUILD ===
# id: test_zfae_gonal_inscription
#   module_name: test_zfae_gonal_inscription
#   module_kind: experiment
#   summary: regression for ZFAE Route A — PrivateGonal determinism, 53→32 whitening bridge, engine PCEA-digest + non-flat tensors, gonal-seed safetensors persistence
#   owner: a0p maintainer
#   public_surface: none
#   internal_surface: none
#   auth_boundary: none
#   storage_boundary: read
#   network_boundary: none
#   user_data_boundary: none
#   admin_only: false
#   tests: self
#   rollout: default_enabled
#   rollback: delete file
# === END MODULE_BUILD ===
# === CONTRACTS ===
# id: test_zfae_gonal_inscription_loads
#   given: module declares its msdmd canon
#   then: the module imports cleanly under the current interpreter
#   class: integration
#   call: a0p_skills.contracts.module_imports_cleanly_holds
# === END CONTRACTS ===
"""Pytest regression for the ZFAE Route A Gonal Inscription decoder."""
import os
import tempfile

from interdependent_lib.zfae.gonal_inscription import (
    PrivateGonal, inscribe_text, whiten_payload, whitened_indices,
    BRIDGE_OUT_WIDTH,
)
from interdependent_lib.zfae.weights import A0ZFAEWeightBank
from interdependent_lib.zfae.inference import A0ZFAEInferenceEngine


def test_private_gonal_is_deterministic_bijection():
    g1 = PrivateGonal.from_seed(b"seed-A")
    g2 = PrivateGonal.from_seed(b"seed-A")
    assert g1.phase == g2.phase and g1.perm == g2.perm
    assert sorted(g1.perm) == list(range(g1.n))
    assert PrivateGonal.from_seed(b"seed-B").perm != g1.perm


def test_advance_changes_rotation_deterministically():
    g = PrivateGonal.from_seed(b"seed-A")
    a = g.advance(1, "deadbeef")
    b = g.advance(1, "deadbeef")
    assert a.phase == b.phase
    assert a.perm == g.perm  # permutation is stable; only phase rotates


def test_whitening_bridge_53_to_32():
    payload = [0.01 * i for i in range(53)]
    w = whiten_payload(payload, b"seed")
    assert isinstance(w, bytes) and len(w) == BRIDGE_OUT_WIDTH
    idx = whitened_indices(w, 53, 100)
    assert len(idx) == 100 and all(0 <= i < 53 for i in idx)


def test_inscribe_text_deterministic_and_digest_sensitive():
    g = PrivateGonal.from_seed(b"seed-A")
    phi = [0.1 * ((i % 7) - 3) for i in range(53)]
    psi = [0.05 * ((i % 5) - 2) for i in range(53)]
    omega = [0.02 * ((i % 3) - 1) for i in range(53)]
    t1, m1 = inscribe_text(g, phi, psi, omega, "abc123")
    t2, _ = inscribe_text(g, phi, psi, omega, "abc123")
    assert t1 == t2 and len(t1) > 0
    assert inscribe_text(g, phi, psi, omega, "zzz999")[0] != t1
    assert {"vertex_idx", "rotation", "pcea_digest_prefix"} <= set(m1)


def test_seam_is_fixed_point_of_perm_and_phase():
    # SPACE/ZERO at position 0 is the Möbius seam — never moved or hidden.
    import math
    for s in (b"seed-A", b"seed-B", b"seed-C", b"morphology"):
        g = PrivateGonal.from_seed(s)
        assert g.perm[0] == 0, "perm must fix the seam (position 0)"
        assert g.arrangement[0] == " ", "position 0 must be SPACE/ZERO"
        # rotation never displaces the seam
        adv = g.advance(7, "deadbeef")
        assert adv.perm[0] == 0
        # an angle landing on the seam emits vertex 0 regardless of phase
        assert g.inscribe(0.0) == 0
        assert adv.inscribe(0.0) == 0
        # the glyph "0" (digit) is NOT the seam — it lives elsewhere
        assert g.arrangement.index("0") != 0


def test_spaces_emitted_as_seam_events_not_deleted():
    # Force a phi/omega field that lands on the seam often; spaces must survive.
    g = PrivateGonal.from_seed(b"seam-emit")
    phi = [0.0 for _ in range(53)]
    omega = [0.0 for _ in range(53)]
    text, meta = inscribe_text(g, phi, [0.0] * 53, omega, "0000", length=40)
    assert "seam_emissions" in meta
    if meta["seam_emissions"] > 0:
        assert " " in text, "seam events must appear as spaces, not be deleted"
    # determinism preserved
    text2, _ = inscribe_text(g, phi, [0.0] * 53, omega, "0000", length=40)
    assert text == text2



    bank = A0ZFAEWeightBank.fresh("route-a-agent")
    eng = A0ZFAEInferenceEngine()
    r = eng.infer(rawPrompt="describe the state", gonal_seed=bank.gonal_seed_bytes)
    assert r["trace"]["decoder"] == "gonal_inscription_v1"
    assert r["trace"]["zfae_decode"]["vertex_idx"] >= 0
    assert r["trace"]["pcea_ciphertext_digest_prefix"]
    assert isinstance(r["trace"]["memory_long_canon"], dict)
    # non-flat: the 53-wide tensors must be carried, not collapsed
    assert len(r["nextSnapshot"]["phi"]) == 53


def test_engine_route_b_without_gonal_seed():
    eng = A0ZFAEInferenceEngine()
    r = eng.infer(rawPrompt="describe the state")
    assert r["trace"]["decoder"] == "template_grammar_v1"
    assert len(r["assistantText"]) > 0


def test_gonal_seed_persists_through_safetensors():
    bank = A0ZFAEWeightBank.fresh("persist-agent")
    gs = bank.gonal_seed_bytes
    with tempfile.TemporaryDirectory() as d:
        p = os.path.join(d, "ck.safetensors")
        bank.save(p)
        loaded = A0ZFAEWeightBank.load(p, "persist-agent")
        assert loaded.gonal_seed_bytes == gs
        assert loaded.zfae_weight_count == 1_223_187
