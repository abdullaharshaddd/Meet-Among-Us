# AI Meeting Intelligence Agent

Bilingual (English–Urdu) meeting intelligence for in-person, multi-speaker meetings. Final-year
project. See `CLAUDE.md` for working rules, `docs/PROJECT_BRIEF.md` for the full project
context, and `docs/DATA_MODEL.md` for the schema contract.

## Layout

| Path | What |
|---|---|
| `/backend` | FastAPI (Python 3.11, `uv`). Layers: `routers` → `services` → `repositories` → `models`/`schemas`/`core`. |
| `/mobile` | Expo (React Native, TypeScript), Expo Router, TanStack Query, Zustand. |
| `/ml` | Separate `uv` package for speaker-embedding / audio work — kept isolated so its heavy deps never land in the API's environment. |
| `/docs` | ADRs (`docs/adr/`), glossary, data model, project brief. |
| `/scripts` | One-off / demo scripts. |

## Commands

```bash
# backend
cd backend && uv sync
cd backend && uv run alembic upgrade head
cd backend && uv run uvicorn app.main:app --reload
cd backend && uv run pytest

# mobile
cd mobile && npx expo start --dev-client
cd mobile && eas build --profile development --platform android
```

Backend needs `backend/.env` — copy `backend/.env.example` and fill in real Supabase/R2/Resend/
Google credentials. Never commit `.env`.
