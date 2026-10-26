"""Unit tests for a0p_skills.msdmd_refactor — refactor_text() and run()."""
from pathlib import Path

import pytest

from a0p_skills.msdmd_refactor import refactor_text, run


# ---------------------------------------------------------------------------
# refactor_text — scaffold insertion
# ---------------------------------------------------------------------------
def test_refactor_text_inserts_all_three_scaffold_blocks():
    text = "def foo(): pass\n"
    result, actions = refactor_text(text, Path("mymod.py"), "mymod.py", "all")
    assert "=== MODULE_BUILD ===" in result
    assert "=== BOUNDARIES ===" in result
    assert "=== CAPABILITIES ===" in result
    assert actions["scaffold"] == ["MODULE_BUILD", "BOUNDARIES", "CAPABILITIES"]


def test_refactor_text_inserts_ratios_bookends():
    text = "x = 1\n"
    result, actions = refactor_text(text, Path("mymod.py"), "mymod.py", "all")
    assert result.count("=== RATIOS ===") == 2
    assert result.count("=== END RATIOS ===") == 2
    assert actions["ratios"] is True


# ---------------------------------------------------------------------------
# refactor_text — idempotency
# ---------------------------------------------------------------------------
def test_refactor_text_idempotent_full_output():
    text = "def bar(): pass\n"
    result1, _ = refactor_text(text, Path("mod.py"), "mod.py", "all")
    result2, actions2 = refactor_text(result1, Path("mod.py"), "mod.py", "all")
    assert result1 == result2
    assert actions2["scaffold"] == []


# ---------------------------------------------------------------------------
# refactor_text — shebang / coding-cookie prefix handling
# ---------------------------------------------------------------------------
def test_refactor_text_shebang_stays_first():
    text = "#!/usr/bin/env python3\nx = 1\n"
    result, _ = refactor_text(text, Path("script.py"), "script.py", "all")
    assert result.splitlines()[0] == "#!/usr/bin/env python3"
    assert "=== RATIOS ===" in result.splitlines()[1]


def test_refactor_text_coding_cookie_stays_first():
    text = "# -*- coding: utf-8 -*-\nx = 1\n"
    result, _ = refactor_text(text, Path("mod.py"), "mod.py", "all")
    assert result.splitlines()[0] == "# -*- coding: utf-8 -*-"
    assert "=== RATIOS ===" in result.splitlines()[1]


def test_refactor_text_shebang_and_coding_cookie_both_stay_first():
    text = "#!/usr/bin/env python3\n# coding: utf-8\nx = 1\n"
    result, _ = refactor_text(text, Path("script.py"), "script.py", "all")
    lines = result.splitlines()
    assert lines[0] == "#!/usr/bin/env python3"
    assert lines[1] == "# coding: utf-8"
    assert "=== RATIOS ===" in lines[2]


# ---------------------------------------------------------------------------
# refactor_text — existing scaffold blocks are not clobbered
# ---------------------------------------------------------------------------
def test_refactor_text_does_not_clobber_existing_module_build():
    existing = (
        "# === MODULE_BUILD ===\n"
        "# id: mymod\n"
        "#   module_name: mymod\n"
        "#   module_kind: custom_kind\n"
        "#   summary: my custom summary\n"
        "#   owner: me\n"
        "#   public_surface: foo\n"
        "#   internal_surface: none\n"
        "#   auth_boundary: high\n"
        "#   storage_boundary: none\n"
        "#   network_boundary: none\n"
        "#   user_data_boundary: none\n"
        "#   admin_only: true\n"
        "#   tests: yes\n"
        "#   rollout: gated\n"
        "#   rollback: delete\n"
        "# === END MODULE_BUILD ===\n"
        "def foo(): pass\n"
    )
    result, actions = refactor_text(existing, Path("mymod.py"), "mymod.py", "all")
    assert "custom_kind" in result
    assert "my custom summary" in result
    assert "MODULE_BUILD" not in actions["scaffold"]


def test_refactor_text_partial_scaffold_inserts_only_missing_blocks():
    # Only BOUNDARIES present; MODULE_BUILD and CAPABILITIES should be added.
    text = (
        "# === BOUNDARIES ===\n"
        "# id: mymod_boundaries\n"
        "#   summary: s\n"
        "#   auth_boundary: none\n"
        "#   storage_boundary: none\n"
        "#   network_boundary: none\n"
        "#   user_data_boundary: none\n"
        "#   admin_only: false\n"
        "#   owner: me\n"
        "# === END BOUNDARIES ===\n"
        "x = 1\n"
    )
    result, actions = refactor_text(text, Path("mymod.py"), "mymod.py", "all")
    assert "MODULE_BUILD" in actions["scaffold"]
    assert "BOUNDARIES" not in actions["scaffold"]
    assert "CAPABILITIES" in actions["scaffold"]


# ---------------------------------------------------------------------------
# refactor_text — ratios strip / recompute
# ---------------------------------------------------------------------------
def test_refactor_text_strips_and_recomputes_existing_ratios():
    # Plant a stale RATIOS block with a bogus value.
    stale = (
        "# === RATIOS ===\n"
        "# id: loc_comments\n"
        "#   summary: lines of code to lines commented\n"
        "#   value: 9999:0\n"
        "#   basis: ratios_runner.compute_loc_comments\n"
        "# === END RATIOS ===\n"
        "x = 1\n"
    )
    result, actions = refactor_text(stale, Path("mod.py"), "mod.py", "ratios")
    assert "9999:0" not in result
    assert actions["ratios"] is True
    # Exactly two RATIOS fences — head and tail.
    assert result.count("=== RATIOS ===") == 2


# ---------------------------------------------------------------------------
# refactor_text — phase filtering
# ---------------------------------------------------------------------------
def test_refactor_text_phase_scaffold_only_does_not_insert_ratios():
    text = "x = 1\n"
    result, actions = refactor_text(text, Path("mod.py"), "mod.py", "scaffold")
    assert actions["ratios"] is False
    assert "=== RATIOS ===" not in result
    assert "=== MODULE_BUILD ===" in result


def test_refactor_text_phase_ratios_only_does_not_insert_scaffold():
    text = "x = 1\n"
    result, actions = refactor_text(text, Path("mod.py"), "mod.py", "ratios")
    assert actions["scaffold"] == []
    assert "=== RATIOS ===" in result
    assert "=== MODULE_BUILD ===" not in result


# ---------------------------------------------------------------------------
# refactor_text — module_kind inference from path
# ---------------------------------------------------------------------------
def test_refactor_text_infers_route_module_kind():
    text = "def handler(): pass\n"
    result, _ = refactor_text(text, Path("routes/main.py"), "routes/main.py", "scaffold")
    assert "module_kind: route" in result


def test_refactor_text_infers_service_module_kind():
    text = "def serve(): pass\n"
    result, _ = refactor_text(text, Path("services/email.py"), "services/email.py", "scaffold")
    assert "module_kind: service" in result


# ---------------------------------------------------------------------------
# run() — dry_run
# ---------------------------------------------------------------------------
def test_run_dry_run_leaves_files_unchanged(tmp_path):
    p = tmp_path / "mod.py"
    p.write_text("x = 1\n", encoding="utf-8")
    rep = run(tmp_path, phase="all", dry_run=True)
    assert p.read_text(encoding="utf-8") == "x = 1\n"
    assert rep["dry_run"] is True
    assert rep["changed_count"] == 1  # would have changed


def test_run_applies_changes_when_not_dry_run(tmp_path):
    p = tmp_path / "mod.py"
    p.write_text("x = 1\n", encoding="utf-8")
    rep = run(tmp_path, phase="all", dry_run=False)
    new_text = p.read_text(encoding="utf-8")
    assert new_text != "x = 1\n"
    assert "=== RATIOS ===" in new_text
    assert rep["changed_count"] == 1


# ---------------------------------------------------------------------------
# run() — unchanged files are not re-reported
# ---------------------------------------------------------------------------
def test_run_does_not_report_unchanged_files(tmp_path):
    p = tmp_path / "mod.py"
    p.write_text("x = 1\n", encoding="utf-8")
    run(tmp_path, phase="all", dry_run=False)
    # Second pass: already-refactored file must not appear in changed list.
    rep2 = run(tmp_path, phase="all", dry_run=False)
    assert rep2["changed_count"] == 0


# ---------------------------------------------------------------------------
# run() — skips non-Python files
# ---------------------------------------------------------------------------
def test_run_skips_non_python_files(tmp_path):
    (tmp_path / "readme.md").write_text("# hello\n", encoding="utf-8")
    (tmp_path / "data.json").write_text("{}\n", encoding="utf-8")
    rep = run(tmp_path, phase="all", dry_run=True)
    assert rep["changed_count"] == 0
    assert rep["skipped_count"] == 0  # non-py files are simply not visited


# ---------------------------------------------------------------------------
# run() — report shape
# ---------------------------------------------------------------------------
def test_run_report_has_required_keys(tmp_path):
    rep = run(tmp_path, phase="all", dry_run=True)
    for key in ("tool", "root", "phase", "dry_run", "generated_at",
                "changed_count", "skipped_count", "changed", "skipped"):
        assert key in rep
    assert rep["tool"] == "msdmd_refactor"
    assert rep["phase"] == "all"


def test_run_report_skipped_count_for_unreadable_file(tmp_path, monkeypatch):
    p = tmp_path / "broken.py"
    p.write_text("x = 1\n", encoding="utf-8")

    original_read_text = Path.read_text

    def boom(self, **kwargs):
        if self == p:
            raise OSError("permission denied")
        return original_read_text(self, **kwargs)

    monkeypatch.setattr(Path, "read_text", boom)
    rep = run(tmp_path, phase="all", dry_run=True)
    assert rep["skipped_count"] == 1
    assert "broken.py" in rep["skipped"][0]
