# === MODULE_BUILD ===
# id: test_lifted_path
#   module_name: test_lifted_path
#   module_kind: test
#   summary: pytest round-trip coverage for the lossless lifted traversal over the
#     157-gonal carrier — encode/decode inversion, repeated-character full revolution,
#     SPACE-as-seam-event, the digit "0" as an ordinary glyph vertex, strict path
#     monotonicity, and off-carrier character refusal
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
# id: test_lifted_path_boundaries
#   summary: pure in-process tests; no network, no storage
#   auth_boundary: none
#   storage_boundary: none
#   network_boundary: none
#   user_data_boundary: none
#   admin_only: false
#   owner: Erin Spencer
# === END BOUNDARIES ===
"""Tests for the lossless lifted text traversal over the 157-gonal carrier."""
from __future__ import annotations
import pytest

from interdependent_lib.gonal.lifted_path import (
    encode_text_path, decode_text_path, vertex_of_char, char_of_vertex,
    is_seam_event, path_vertices, ARITY, ORIGIN, CarrierCharError,
)


CASES = ["aa", "aaa", "a a", "  ", "0", "10 01"]


@pytest.mark.parametrize("text", CASES)
def test_round_trip_is_lossless(text):
    assert decode_text_path(encode_text_path(text)) == text


@pytest.mark.parametrize("text", CASES)
def test_path_is_strictly_monotonic(text):
    p = encode_text_path(text)
    assert all(p[i] < p[i + 1] for i in range(len(p) - 1))


def test_repeat_costs_full_revolution():
    p = encode_text_path("aa")
    assert p[1] - p[0] == ARITY
    p3 = encode_text_path("aaa")
    assert p3[1] - p3[0] == ARITY and p3[2] - p3[1] == ARITY


def test_space_is_seam_event():
    assert vertex_of_char(" ") == ORIGIN == 0
    sp = encode_text_path(" ")
    assert is_seam_event(sp[0])
    assert decode_text_path(sp) == " "
    # two spaces are both preserved, not collapsed/deleted
    assert decode_text_path(encode_text_path("  ")) == "  "


def test_digit_zero_is_ordinary_glyph_not_seam():
    assert vertex_of_char("0") != ORIGIN
    assert char_of_vertex(vertex_of_char("0")) == "0"
    assert decode_text_path(encode_text_path("0")) == "0"


def test_path_vertices_and_seam_helpers():
    p = encode_text_path("a a")
    verts = path_vertices(p)
    assert verts[1] == ORIGIN  # the middle space sits on the seam
    assert is_seam_event(p[1]) and not is_seam_event(p[0])


def test_off_carrier_char_refused():
    with pytest.raises(CarrierCharError):
        vertex_of_char("\u2603")  # snowman: not on the carrier
    with pytest.raises(CarrierCharError):
        encode_text_path("hi \u2603")


def test_longer_mixed_round_trip():
    text = "the river 10 01 and 0 again a a"
    assert decode_text_path(encode_text_path(text)) == text
