# Test Credentials — a0p

## Admin (seeded from `.env` on boot — idempotent)

| Field | Value |
|---|---|
| username | `wayseer` |
| email | `wayseer@interdependentway.org` |
| passphrase | `nospecialcharacters` |
| role | `admin` |

The admin user is re-seeded on every backend start from these `.env` vars:
- `ADMIN_USERNAME=wayseer`
- `ADMIN_EMAIL=wayseer@interdependentway.org`
- `ADMIN_PASSWORD=nospecialcharacters`

## Test user (created by testing-agent flows)

| Field | Value |
|---|---|
| username | `alice` |
| email | `alice@example.com` |
| passphrase | `sixteenchars-and-more-passphrase` |
| role | `user` |

If the user does not yet exist, register them with
`POST /api/auth/register` body `{"username":"alice","email":"alice@example.com","passphrase":"sixteenchars-and-more-passphrase"}`.

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
