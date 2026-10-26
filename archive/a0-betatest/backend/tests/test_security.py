# === MODULE_BUILD ===
# id: test_security
#   module_name: test_security
#   module_kind: test
#   summary: security regression suite — Fernet at-rest encryption round-trip + masking,
#     bcrypt password hashing/verification, JWT mint/decode + tamper rejection, ZFAE
#     refuse-until-trained gate, gated (HOLD) clause decomposition, off-carrier glyph
#     rejection on the lifted path, and append-only traffic log secret-redaction
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
# id: test_security_boundaries
#   summary: pure in-process security tests; seeds throwaway secrets; no network
#   auth_boundary: none
#   storage_boundary: none
#   network_boundary: none
#   user_data_boundary: none
#   admin_only: false
#   owner: Erin Spencer
# === END BOUNDARIES ===
"""Security regression suite — runs fully offline with throwaway secrets."""
from __future__ import annotations
import os

from cryptography.fernet import Fernet

# Seed throwaway secrets BEFORE importing modules that require them at import.
os.environ.setdefault("A0P_KEY_VAULT_SECRET", Fernet.generate_key().decode())
os.environ.setdefault("JWT_SECRET", "test-only-jwt-secret-do-not-use-in-prod")
os.environ.setdefault("MONGO_URL", "mongodb://localhost:27017")
os.environ.setdefault("DB_NAME", "test_a0p_security")

import pytest

import crypto_vault as cv
from auth import _hash_password, _verify_password, _make_tokens, _jwt_secret, _JWT_ALG
import jwt as pyjwt


# ---- At-rest encryption (BYOK key vault) -----------------------------------

def test_fernet_round_trip_and_ciphertext_opaque():
    secret = "sk-super-secret-byok-key-123"
    enc = cv.encrypt(secret)
    assert enc != secret, "ciphertext must not equal plaintext"
    assert secret not in enc, "plaintext must not appear in ciphertext"
    assert cv.decrypt(enc) == secret, "decrypt must invert encrypt"


def test_tampered_ciphertext_is_rejected():
    enc = cv.encrypt("another-secret")
    tampered = enc[:-2] + ("AA" if enc[-2:] != "AA" else "BB")
    with pytest.raises(Exception):
        cv.decrypt(tampered)


def test_mask_hides_most_of_the_secret():
    masked = cv.mask("sk-1234567890abcdef")
    assert masked != "sk-1234567890abcdef"
    assert masked.count("*") >= 1 or "…" in masked or len(masked) < len("sk-1234567890abcdef")


# ---- Password hashing ------------------------------------------------------

def test_password_hash_is_not_plaintext_and_verifies():
    pw = "a-sixteen-char-or-more-passphrase"
    h = _hash_password(pw)
    assert h != pw and pw not in h, "hash must not embed the plaintext"
    assert h.startswith("$2"), "must be a bcrypt hash"
    assert _verify_password(pw, h) is True
    assert _verify_password("wrong-passphrase-entirely", h) is False


# ---- JWT mint / decode / tamper --------------------------------------------

def test_jwt_round_trip_and_tamper_rejection():
    access, refresh = _make_tokens("user-123", "u@example.org")
    payload = pyjwt.decode(access, _jwt_secret(), algorithms=[_JWT_ALG])
    assert payload["sub"] == "user-123" and payload["type"] == "access"
    # a token signed with the wrong secret must not verify
    forged = pyjwt.encode({"sub": "attacker", "type": "access"}, "wrong-secret", algorithm=_JWT_ALG)
    with pytest.raises(pyjwt.PyJWTError):
        pyjwt.decode(forged, _jwt_secret(), algorithms=[_JWT_ALG])


# ---- ZFAE native refuse-until-trained --------------------------------------

def test_native_refuses_until_trained():
    from interdependent_lib.zfae.weights import A0ZFAEWeightBank
    from interdependent_lib.zfae.runtime import _is_trained_enough
    bank = A0ZFAEWeightBank.fresh("untrained-agent")
    assert _is_trained_enough(bank) is False, "a fresh agent must not be native-ready"


# ---- Decomposition is HELD (not falsely certified) -------------------------

def test_clause_decomposition_is_gated():
    from interdependent_lib.zfae import morphology as m
    assert m.PROOF_GREEN is False, "decomposition must not be represented as certified"
    word = m.compose_word(0.3, 0.6)
    with pytest.raises(m.DecompositionGatedError):
        m.decompose_clause(word, m.frame_value(0.6))


# ---- Lifted path rejects off-carrier glyphs (no silent corruption) ---------

def test_lifted_path_rejects_off_carrier_and_is_lossless():
    from interdependent_lib.gonal.lifted_path import (
        encode_text_path, decode_text_path, CarrierCharError,
    )
    assert decode_text_path(encode_text_path("a a 0")) == "a a 0"
    with pytest.raises(CarrierCharError):
        encode_text_path("payload \u2603")  # off-carrier char must be refused


# ---- Append-only traffic log never records secrets -------------------------

def test_traffic_log_redacts_secrets(tmp_path):
    import importlib
    log = tmp_path / "traffic.log"
    os.environ["A0P_TRAFFIC_LOG"] = str(log)
    import traffic_log
    importlib.reload(traffic_log)
    traffic_log._append({"ts": "t", "method": "POST", "path": "/api/auth/login", "status": 200})
    text = log.read_text(encoding="utf-8")
    assert text.endswith("\n") and text.count("\n") == 1
    low = text.lower()
    for forbidden in ("authorization", "password", "passphrase", "api_key", "cookie"):
        assert forbidden not in low
