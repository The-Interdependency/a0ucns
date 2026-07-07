# Test Credentials — a0p

> **Do not commit real secrets to this file.** Values below are placeholders.
> Set the actual admin credentials via environment variables (`.env`, not tracked)
> or your deployment secret store. `seed_admin()` in `backend/auth/__init__.py`
> **resets the admin password hash to `ADMIN_PASSWORD` on every backend start**, so
> any value written here that matches a live deployment is a working admin login.

## Admin (seeded from `.env` on boot — idempotent)

| Field | Value |
|---|---|
| username | `<ADMIN_USERNAME>` |
| email | `<ADMIN_EMAIL>` |
| passphrase | `<ADMIN_PASSWORD>` (set in `.env`; never commit) |
| role | `admin` |

The admin user is re-seeded on every backend start from these `.env` vars
(kept out of version control):
- `ADMIN_USERNAME=<your-admin-username>`
- `ADMIN_EMAIL=<your-admin-email>`
- `ADMIN_PASSWORD=<a-strong-secret-not-checked-in>`

## Test user (created by testing-agent flows)

| Field | Value |
|---|---|
| username | `alice` |
| email | `alice@example.com` |
| passphrase | `<TEST_USER_PASSPHRASE>` (choose locally; ≥ 16 chars) |
| role | `user` |

If the user does not yet exist, register them with
`POST /api/auth/register` body
`{"username":"alice","email":"alice@example.com","passphrase":"<TEST_USER_PASSPHRASE>"}`.

## Auth endpoints

- `POST /api/auth/register` — `{ username, email, passphrase }` → user + httpOnly access/refresh cookies
- `POST /api/auth/login` — `{ identifier, passphrase }` (identifier may be username OR email)
- `POST /api/auth/logout`
- `GET /api/auth/me`
- `POST /api/auth/refresh`
- `POST /api/auth/oauth/google-session` — `{ session_id }` (Emergent Google)
- `GET /api/auth/oauth/github/start` (returns redirect URL)
- `POST /api/auth/oauth/github/callback` — `{ code }`

## Frontend routes

- Public: `/`, `/login`, `/register`, `/spec`
- Protected (require login): `/workspace`, `/agents`, `/sentinels`, `/overrides`, `/inspector`, `/inventory`, `/keys`, `/custom-keys`, `/vault`, `/drafts`

## Demo quota

- Per-user soft budget: `EMERGENT_DEMO_DAILY_TOKEN_BUDGET=25000` tokens / UTC day, reset 00:00 UTC.
- `GET /api/demo-quota` returns `{ day, budget, used, remaining, fits }`.
