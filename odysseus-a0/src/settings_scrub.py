# === RATIOS ===
# id: loc_comments
#   summary: lines of code to lines commented
#   value: 27:48
#   basis: ratios_runner.compute_loc_comments
#
# id: imports_exports
#   summary: import statements to public exports
#   value: 0:2
#   basis: ratios_runner.compute_imports_exports
#
# id: calls_definitions
#   summary: call sites to definitions
#   value: 11:3
#   basis: ratios_runner.compute_calls_definitions
# === END RATIOS ===
# === MODULE_BUILD ===
# id: settings_scrub
#   module_name: settings_scrub
#   module_kind: hmmm
#   summary: Secret-scrubbing for settings exposed to non-admin / unauthenticated callers.
#   owner: hmmm
#   public_surface: is_secret_key, scrub_settings
#   internal_surface: _scrub_value
#   auth_boundary: hmmm
#   storage_boundary: hmmm
#   network_boundary: hmmm
#   user_data_boundary: hmmm
#   admin_only: hmmm
#   tests: hmmm
#   rollout: hmmm
#   rollback: hmmm
# === END MODULE_BUILD ===
# === BOUNDARIES ===
# id: settings_scrub_boundaries
#   summary: Secret-scrubbing for settings exposed to non-admin / unauthenticated callers.
#   auth_boundary: hmmm
#   storage_boundary: hmmm
#   network_boundary: hmmm
#   user_data_boundary: hmmm
#   admin_only: hmmm
#   owner: hmmm
# === END BOUNDARIES ===
# === CAPABILITIES ===
# id: settings_scrub
#   summary: Secret-scrubbing for settings exposed to non-admin / unauthenticated callers.
#   exposes: is_secret_key, scrub_settings
# === END CAPABILITIES ===
"""Secret-scrubbing for settings exposed to non-admin / unauthenticated callers.

Deliberately dependency-light (stdlib only) and separate from
``routes/auth_routes.py`` so it can be imported and unit-tested without dragging
in the FastAPI app / auth / database import chain.

``/api/auth/settings`` is auth-exempt — the frontend (and the pre-login page)
read it for keybinds + TTS prefs, so non-admin and unauthenticated callers get a
*scrubbed* copy. Secrets (provider API keys, IMAP/SMTP passwords, OAuth tokens)
must NOT leak to them — load-bearing when the app is reachable over a Cloudflare
tunnel / reverse proxy. Scrubbing is deep (recurses nested dicts/lists) and keyed
on secret-shaped names.
"""

_SECRET_KEY_PATTERNS = (
    "_api_key", "_apikey", "_password", "_passwd", "_pass", "_pwd",
    "_secret", "_client_secret", "_token", "_access_token", "_refresh_token",
    "_credential", "_credentials", "_key",
)
_SECRET_KEY_ALLOW = ("google_pse_cx",)  # public identifiers, not secrets


def is_secret_key(name: str) -> bool:
    n = (name or "").lower()
    if n in _SECRET_KEY_ALLOW:
        return False
    return any(n.endswith(p) or n == p.lstrip("_") for p in _SECRET_KEY_PATTERNS)


def _scrub_value(key, value):
    """Mask secret-shaped leaves, recursing into nested dicts/lists so a secret
    stored under a non-secret parent key (e.g.
    ``{"email_account": {"smtp_password": "..."}}``) is still blanked. Only
    non-empty *string* values are blanked; presence is preserved."""
    if isinstance(value, dict):
        return {
            k: ("" if (is_secret_key(k) and isinstance(v, str) and v)
                else _scrub_value(k, v))
            for k, v in value.items()
        }
    if isinstance(value, list):
        return [_scrub_value(key, item) for item in value]
    if is_secret_key(key) and isinstance(value, str) and value:
        return ""
    return value


def scrub_settings(settings: dict) -> dict:
    """Return a copy of ``settings`` with secret-shaped values masked (deep)."""
    if not isinstance(settings, dict):
        return {}
    return {k: _scrub_value(k, v) for k, v in (settings or {}).items()}
# === RATIOS ===
# id: loc_comments
#   summary: lines of code to lines commented
#   value: 27:48
#   basis: ratios_runner.compute_loc_comments
#
# id: imports_exports
#   summary: import statements to public exports
#   value: 0:2
#   basis: ratios_runner.compute_imports_exports
#
# id: calls_definitions
#   summary: call sites to definitions
#   value: 11:3
#   basis: ratios_runner.compute_calls_definitions
# === END RATIOS ===
