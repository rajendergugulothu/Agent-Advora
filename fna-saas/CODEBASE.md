# Advora — Codebase Documentation

A multi-tenant SaaS platform for financial advisors and agencies. Users connect their WhatsApp and Instagram, and every day the platform generates AI-written finance content, sends it to WhatsApp for approval, and publishes it to Instagram on approval. Post analytics are tracked at 24h, 72h, and 7d after posting, and fed back into the AI to improve future content over time.

---

## Table of Contents

- [Project Structure](#project-structure)
- [How It Works — Full Flow](#how-it-works--full-flow)
- [Backend Deep Dive](#backend-deep-dive)
- [Frontend Deep Dive](#frontend-deep-dive)
- [Database Schema](#database-schema)
- [Environment Variables](#environment-variables)
- [Before You Start Working](#before-you-start-working)
- [Running Locally](#running-locally)
- [Key Design Decisions](#key-design-decisions)
- [Common Pitfalls](#common-pitfalls)

---

## Project Structure

```
fna-saas/
├── backend/                    # FastAPI (Python)
│   ├── app/
│   │   ├── main.py             # App entry point, lifespan, middleware
│   │   ├── api/
│   │   │   └── v1/
│   │   │       ├── router.py   # Mounts all route modules
│   │   │       ├── deps.py     # Shared FastAPI dependencies (auth, db)
│   │   │       ├── users.py    # Profile, settings, scheduler toggle
│   │   │       ├── drafts.py   # Draft list, detail, manual trigger
│   │   │       ├── instagram.py# OAuth connect/callback/status/disconnect
│   │   │       └── webhook.py  # WhatsApp incoming button replies
│   │   ├── core/
│   │   │   ├── config.py       # Pydantic Settings — all env vars loaded here
│   │   │   ├── security.py     # Fernet token encryption + Meta HMAC verify
│   │   │   └── logging.py      # structlog (JSON in prod, console in dev)
│   │   ├── db/
│   │   │   ├── database.py     # Async SQLAlchemy engine + session factory
│   │   │   └── models.py       # ORM models mirroring Supabase schema
│   │   └── services/
│   │       ├── scheduler.py    # APScheduler — per-user jobs, analytics, token refresh
│   │       ├── content.py      # OpenAI content generation + theme selection
│   │       ├── image.py        # DALL-E 3 image generation + Cloudinary upload
│   │       ├── instagram.py    # Instagram Graph API (OAuth, publish, insights)
│   │       └── whatsapp.py     # WhatsApp Cloud API (send draft, send text)
│   ├── requirements.txt
│   ├── .env.example            # Template — copy to .env and fill in
│   └── venv/                   # Python virtual environment (not committed)
│
├── frontend/                   # Next.js 16 (TypeScript + Tailwind)
│   ├── app/
│   │   ├── layout.tsx          # Root layout
│   │   ├── page.tsx            # Root redirect → /dashboard or /login
│   │   ├── (auth)/
│   │   │   ├── login/          # Login page
│   │   │   └── signup/         # Signup page (captures full_name, company_name)
│   │   └── dashboard/
│   │       ├── layout.tsx      # Sidebar navigation
│   │       ├── page.tsx        # Overview — stat cards + recent drafts
│   │       ├── drafts/         # Paginated draft list with analytics
│   │       ├── analytics/      # Charts (Recharts) + top themes table
│   │       ├── connect/        # Instagram OAuth connect/disconnect UI
│   │       └── settings/       # Profile, WhatsApp, schedule settings
│   ├── lib/
│   │   ├── supabase.ts         # Supabase browser client
│   │   └── api.ts              # Typed API client + all TypeScript interfaces
│   ├── .env.local.example      # Template — copy to .env.local
│   └── package.json
│
└── supabase/
    └── migrations/
        ├── 001_initial_schema.sql  # All tables and enums
        ├── 002_indexes.sql         # Performance indexes
        ├── 003_rls_policies.sql    # Row Level Security (users see only their data)
        └── 004_functions.sql       # DB functions, triggers, performance views
```

---

## How It Works — Full Flow

### 1. User Signs Up
- User registers via the frontend (Supabase Auth handles email/password).
- The `handle_new_user` Postgres trigger (in `004_functions.sql`) automatically creates a `user_profiles` row when a new auth user is created.
- The user fills in their profile: name, company, WhatsApp number, preferred post time, and timezone.

### 2. Instagram Connection
```
User clicks "Connect Instagram" in dashboard
  → Frontend calls GET /api/v1/instagram/connect
  → Backend returns a Meta OAuth URL with scopes:
      instagram_basic, instagram_content_publish,
      instagram_manage_insights, pages_show_list, pages_read_engagement
  → User is redirected to Meta to grant permissions
  → Meta redirects to GET /api/v1/instagram/callback?code=...&state=<user_id>
  → Backend:
      1. Exchanges code → short-lived token (valid 1h)
      2. Exchanges short-lived → long-lived token (valid 60 days)
      3. Gets Facebook Pages → finds linked Instagram Business Account
      4. Fetches Instagram username and profile picture
      5. Stores encrypted credentials in instagram_connections table
  → Redirects user to frontend /dashboard/connect?status=success
```

> **Important:** The Instagram account must be a **Business or Creator account** linked to a **Facebook Page**. Personal Instagram accounts will not work.

### 3. Scheduler Activation
- User enables the scheduler from Settings.
- Backend registers an APScheduler `CronTrigger` job for that user: `daily_post_{user_id}`.
- The job fires at the user's configured hour/minute in their timezone every day.
- Each user has a completely isolated job — one user's failure does not affect others.

### 4. Daily Content Generation (The Core Loop)
```
CronTrigger fires for user
  → scheduler._daily_generate_and_send(user_id)
  → content.generate_post(supabase, user_id)
      → Fetches top/worst performing themes from DB (performance feedback loop)
      → Picks a theme: 20% advisor authority, 55% top-performers, 25% exploration
      → Calls OpenAI GPT-4o-mini with structured prompt
      → Returns: theme, audience, hook, caption, hashtags, image_concept, post_type,
                 carousel_slides (if carousel)
  → Saves draft to DB with status = "pending"
  → whatsapp.send_draft_for_approval(post, draft_id, recipient)
      → Sends interactive WhatsApp message with two buttons:
          [Approve & Post]  [Regenerate]
        Button IDs: "APPROVE_{draft_id}" and "REGENERATE_{draft_id}"
```

### 5. User Approves or Regenerates via WhatsApp
```
User taps a button on WhatsApp
  → Meta sends webhook POST to /api/v1/webhook
  → Backend verifies HMAC signature (X-Hub-Signature-256)
  → Parses button reply ID → extracts action + draft_id
  → Looks up draft → gets user_id → routes to scheduler

If APPROVE:
  → Checks Instagram connection is active
  → Sets draft status = "approved"
  → Generates image(s):
      Single: DALL-E 3 → Cloudinary → public URL
      Carousel: N images concurrently → Cloudinary
  → Publishes to Instagram via Graph API:
      Single: create media container → publish
      Carousel: create N child containers (wait 30s) → create carousel → publish
  → Saves PostResult (instagram_post_id, image_url, etc.)
  → Sets draft status = "posted"
  → Schedules analytics jobs for 24h, 72h, 7d
  → Sends success WhatsApp message with Instagram link

If REGENERATE:
  → Sets draft status = "rejected"
  → Immediately calls _daily_generate_and_send again for a fresh draft
```

### 6. Analytics Tracking
```
Every 15 minutes: scheduler._run_due_analytics_jobs()
  → Queries analytics_jobs WHERE status = "scheduled" AND scheduled_for <= now
  → For each due job:
      → Fetches Instagram Insights API (impressions, reach, likes, comments, shares, saves)
      → Saves to post_analytics table
      → Marks job as "completed"
```

### 7. Performance Feedback Loop
- Postgres functions `get_top_performing_themes()` and `get_worst_performing_themes()` rank themes by engagement rate per user.
- Every time content is generated, these are called → the results are injected into the OpenAI prompt.
- The AI is told which themes resonate and which underperformed for *this specific advisor's audience*.
- Over time, content quality improves automatically per user.

### 8. Token Refresh
- Instagram long-lived tokens expire in 60 days.
- Every night at 3 AM UTC: `scheduler._refresh_expiring_tokens()` refreshes any token expiring within 15 days.
- New encrypted token is saved back to `instagram_connections`.

---

## Backend Deep Dive

### Authentication
- Supabase handles all auth (sign up, sign in, sessions).
- The frontend sends the Supabase JWT as a `Bearer` token in every API request.
- `deps.py → get_current_user_id()` calls `supabase.auth.get_user(token)` to verify.
- No custom JWT logic exists — Supabase is the single source of truth.

### Token Encryption
All OAuth tokens (Instagram access token, account ID, WhatsApp credentials) are encrypted before being stored in the database using **Fernet symmetric encryption** (`cryptography` library).

- `ENCRYPTION_KEY` in `.env` must be a 64-character hex string (= 32 bytes).
- `security.py` derives the Fernet key by decoding that hex and base64-encoding it.
- Generate a key: `python -c "import secrets; print(secrets.token_hex(32))"`
- **Never store raw tokens in the DB. Always use `encrypt_token()` before saving and `decrypt_token()` before using.**

### Database Sessions
- SQLAlchemy async sessions are used for all DB operations.
- `get_db()` — FastAPI dependency that yields a session per request (auto-committed and closed).
- `AsyncSessionFactory` — used directly in background tasks and the scheduler (outside of request scope).
- All sessions use `expire_on_commit=False` so objects are accessible after commit.

### Scheduler (APScheduler)
- `SchedulerService` is a **singleton** — always access it via `get_scheduler()`, never instantiate directly.
- Created once in `main.py` lifespan, started with `await get_scheduler().start()`.
- The async Supabase client (`self._supabase`) is created inside `start()` and reused across all jobs.
- Each user's daily job ID is `daily_post_{user_id}` — registering with the same ID replaces the existing job.

### Content Generation
- `content.py` contains **200+ themes** across 21 categories (new job income, budgeting, retirement, real estate, taxes, insurance, estate planning, etc.).
- Categories weight: 80% educational (builds audience), 20% advisor authority (builds personal brand).
- Theme selection avoids worst performers and leans toward top performers per user.
- OpenAI returns structured JSON — `generate_post()` validates the response before returning.

### Rate Limiting
- `slowapi` applies per-IP rate limiting (default: 60 requests/minute).
- Configurable via `RATE_LIMIT_PER_MINUTE` env var.

### Logging
- `structlog` with JSON output in production, colored console in development.
- Every significant operation logs a structured event with relevant context fields.
- Sentry integration is optional — set `SENTRY_DSN` to enable.

---

## Frontend Deep Dive

### Auth Flow
- Supabase SSR handles session cookies.
- `lib/supabase.ts` — browser client (used in client components).
- The dashboard layout checks session on every render — unauthenticated users are redirected to `/login`.

### API Client (`lib/api.ts`)
- All backend calls go through the typed API client.
- Automatically attaches the Supabase session JWT as `Authorization: Bearer <token>`.
- All response types are defined as TypeScript interfaces in this file.
- **If you add a new backend endpoint, add the corresponding method and interface here.**

### Pages Overview
| Route | Purpose |
|---|---|
| `/` | Redirects to `/dashboard` or `/login` |
| `/login` | Email/password sign in |
| `/signup` | Register + capture name and company |
| `/dashboard` | Overview: stat cards, recent drafts |
| `/dashboard/drafts` | Paginated list, status filter, expand for analytics |
| `/dashboard/analytics` | Recharts line/bar charts, top themes table |
| `/dashboard/connect` | Instagram OAuth connect/disconnect |
| `/dashboard/settings` | Profile, WhatsApp number, post time, scheduler toggle |

---

## Database Schema

### Tables

| Table | Purpose |
|---|---|
| `user_profiles` | One row per user. Stores settings, WhatsApp number, post time, timezone. |
| `instagram_connections` | One per user. Stores encrypted Instagram tokens and account info. |
| `drafts` | Every generated content piece. Tracks status through the approval lifecycle. |
| `post_results` | Created when a draft is successfully posted. Stores post ID and image URLs. |
| `post_analytics` | One row per post per fetch stage (24h, 72h, 7d). Stores engagement metrics. |
| `analytics_jobs` | Scheduled fetch tasks. Polled every 15 minutes by the scheduler. |
| `webhook_events` | Raw log of all incoming WhatsApp webhook payloads (for audit and debugging). |

### Draft Status Lifecycle
```
pending → approved → posting → posted
        ↘ rejected             ↘ image_failed
                               ↘ post_failed
```

### Row Level Security (RLS)
- RLS is enabled on all tables.
- Users can only read/write their own rows (`user_id = auth.uid()`).
- `webhook_events` is only accessible via the service role key (backend only).
- The backend uses the **service role key** (bypasses RLS) for all operations.
- The frontend uses the **anon key** (subject to RLS) for direct Supabase calls.

### Key Postgres Functions (004_functions.sql)
- `handle_new_user()` — trigger that auto-creates `user_profiles` row on signup.
- `set_updated_at()` — trigger that keeps `updated_at` current on every update.
- `get_top_performing_themes(p_user_id, p_limit)` — returns best themes by engagement rate.
- `get_worst_performing_themes(p_user_id, p_limit)` — returns worst themes.
- `content_performance` — view joining drafts, post_results, and analytics.

---

## Environment Variables

### Backend (`.env`)

| Variable | Required | Description |
|---|---|---|
| `ENVIRONMENT` | No | `development` / `staging` / `production`. Default: `development` |
| `SUPABASE_URL` | Yes | Your Supabase project URL |
| `SUPABASE_ANON_KEY` | Yes | Public anon key (used to verify tokens) |
| `SUPABASE_SERVICE_ROLE_KEY` | Yes | Service role key — bypasses RLS. Keep secret. |
| `DATABASE_URL` | Yes | `postgresql+asyncpg://postgres:<pass>@db.<ref>.supabase.co:5432/postgres` |
| `ENCRYPTION_KEY` | Yes | 64-char hex string. Generate: `python -c "import secrets; print(secrets.token_hex(32))"` |
| `OPENAI_API_KEY` | Yes | OpenAI API key (needs GPT-4o-mini and DALL-E 3 access) |
| `OPENAI_TEXT_MODEL` | No | Default: `gpt-4o-mini` |
| `OPENAI_IMAGE_MODEL` | No | Default: `dall-e-3` |
| `CLOUDINARY_CLOUD_NAME` | Yes | Cloudinary cloud name |
| `CLOUDINARY_API_KEY` | Yes | Cloudinary API key |
| `CLOUDINARY_API_SECRET` | Yes | Cloudinary API secret |
| `CLOUDINARY_UPLOAD_PRESET` | No | Default: `advora_posts` (create this preset in Cloudinary dashboard) |
| `WHATSAPP_PHONE_NUMBER_ID` | Yes | Meta WhatsApp phone number ID |
| `WHATSAPP_ACCESS_TOKEN` | Yes | Permanent WhatsApp system user access token |
| `WHATSAPP_APP_SECRET` | Yes | Meta app secret (used to verify webhook signatures) |
| `WHATSAPP_WEBHOOK_VERIFY_TOKEN` | Yes | Any random string you choose — must match what you set in Meta dashboard |
| `META_APP_ID` | Yes | Meta app ID (for Instagram OAuth) |
| `META_APP_SECRET` | Yes | Meta app secret |
| `META_OAUTH_REDIRECT_URI` | Yes | Must match exactly what's registered in Meta app settings. e.g. `https://yourdomain.com/api/v1/instagram/callback` |
| `FRONTEND_URL` | No | Default: `http://localhost:3000`. Used for OAuth redirect after Instagram connect. |
| `SENTRY_DSN` | No | Sentry DSN for error tracking. Leave empty to disable. |
| `RATE_LIMIT_PER_MINUTE` | No | Default: `60` |
| `ALLOWED_ORIGINS` | No | Default: `["http://localhost:3000"]` |

### Frontend (`.env.local`)

| Variable | Required | Description |
|---|---|---|
| `NEXT_PUBLIC_SUPABASE_URL` | Yes | Same as backend `SUPABASE_URL` |
| `NEXT_PUBLIC_SUPABASE_ANON_KEY` | Yes | Same as backend `SUPABASE_ANON_KEY` |
| `NEXT_PUBLIC_API_URL` | Yes | Backend API base URL. e.g. `http://localhost:8000/api/v1` |

---

## Before You Start Working

Go through this checklist before writing any code.

### 1. Understand the external services
The platform depends on 5 external services. Know what each one does:
- **Supabase** — database, auth, and RLS. Migrations live in `supabase/migrations/`.
- **OpenAI** — GPT-4o-mini for text content, DALL-E 3 for images.
- **Cloudinary** — hosts generated images (Instagram requires a public HTTPS URL).
- **Meta (WhatsApp)** — sends draft approval messages to users' phones.
- **Meta (Instagram Graph API)** — publishes posts and fetches engagement analytics.

### 2. Check the Meta App configuration
If Instagram connect or webhooks are broken, check these in the Meta Developer dashboard:
- App is in **Live** mode (not Development) — otherwise only test users can connect.
- `META_OAUTH_REDIRECT_URI` in `.env` exactly matches the URI registered under **Facebook Login for Business → Valid OAuth Redirect URIs**.
- Instagram OAuth scopes are approved: `instagram_basic`, `instagram_content_publish`, `instagram_manage_insights`, `pages_show_list`, `pages_read_engagement`.
- WhatsApp webhook URL is set and verified (`WHATSAPP_WEBHOOK_VERIFY_TOKEN` matches).
- WhatsApp webhook is subscribed to `messages` field.

### 3. Check the database migrations
All 4 migration files must be applied to your Supabase project **in order**:
```
001_initial_schema.sql  → tables and enums
002_indexes.sql         → performance indexes
003_rls_policies.sql    → row level security
004_functions.sql       → triggers and Postgres functions
```
If you add a new table or column, create a new numbered migration file. **Never edit existing migrations.**

### 4. Check the encryption key
The `ENCRYPTION_KEY` must be the same across all environments that share a database. If you rotate it, all existing encrypted tokens in the DB become unreadable. Users would need to reconnect Instagram.

### 5. Verify the Cloudinary upload preset
The Cloudinary upload preset (`advora_posts` by default) must exist in your Cloudinary dashboard and be set to **unsigned** mode. If images fail to upload, check this first.

### 6. Understand the singleton scheduler
`SchedulerService` is a singleton — `get_scheduler()` always returns the same instance. It is started once in the FastAPI lifespan (`main.py`). If you need to add a new scheduled job:
- Add it inside `SchedulerService.start()` or as a new method.
- Never instantiate `SchedulerService` directly — always use `get_scheduler()`.

### 7. Know the token encryption rule
Every OAuth token written to the DB must go through `encrypt_token()`. Every token read from the DB for use must go through `decrypt_token()`. The DB never holds plaintext credentials.

### 8. Understand RLS — backend uses service role
The backend bypasses RLS by using `SUPABASE_SERVICE_ROLE_KEY`. This means the backend is responsible for enforcing user isolation in code (e.g. `WHERE user_id = ?`). Never return data from one user to another. Check every query that fetches user-specific data.

### 9. Instagram account requirements
When testing Instagram connect, the Instagram account must be:
- A **Business** or **Creator** account (not a personal account).
- Linked to a **Facebook Page** that the test user manages.
- The Facebook Page must be connected to the Instagram account in Instagram/Facebook settings.

### 10. Check that all dependencies are installed
```bash
# Backend
cd backend
venv/Scripts/pip install -r requirements.txt   # Windows
# or
venv/bin/pip install -r requirements.txt       # Mac/Linux

# Frontend
cd frontend
npm install
```

---

## Running Locally

### Backend
```bash
cd fna-saas/backend

# Create virtual environment (first time only)
python -m venv venv

# Activate
venv\Scripts\activate          # Windows
source venv/bin/activate       # Mac/Linux

# Install dependencies
pip install -r requirements.txt

# Copy and fill in environment variables
cp .env.example .env
# Edit .env with your credentials

# Start the server
uvicorn app.main:app --reload --port 8000
```

API docs available at: `http://localhost:8000/docs` (only in non-production mode)

### Frontend
```bash
cd fna-saas/frontend

# Install dependencies
npm install

# Copy and fill in environment variables
cp .env.local.example .env.local
# Edit .env.local with your Supabase URL, anon key, and API URL

# Start dev server
npm run dev
```

Frontend available at: `http://localhost:3000`

### Supabase Migrations
Run all migration files in the Supabase SQL Editor in order, or use the Supabase CLI:
```bash
supabase db push
```

---

## Key Design Decisions

**Why APScheduler instead of a task queue (Celery/Redis)?**
The app is self-contained with no external queue infrastructure needed. APScheduler with `AsyncIOScheduler` runs inside the FastAPI process, which is sufficient for the current scale. Each user gets an isolated `CronTrigger` job so one user's failure doesn't affect others.

**Why Fernet encryption for tokens instead of a secrets vault?**
Simple, dependency-free, and sufficient for this use case. The encryption key is stored in the environment — the same place you'd store a vault access credential anyway. The key consideration is key rotation: rotating the key requires re-encrypting all stored tokens.

**Why Supabase for auth instead of custom JWT?**
Supabase Auth provides email/password auth, session management, and refresh token rotation out of the box. The backend verifies tokens with `auth.get_user(token)` — no JWT secret management needed.

**Why is `user_profiles.id` the same as `auth.users.id`?**
The `handle_new_user` trigger creates the profile with the same UUID as the Supabase auth user. This makes joins trivial and ensures the backend can always resolve `user_id` ↔ `auth.uid()`.

**Why is the WhatsApp number stored on the platform, not per-session?**
The platform sends from one WhatsApp Business number to each user's personal number. Users register their personal WhatsApp number in their profile. The platform's WhatsApp credentials (phone number ID, access token) are global settings in `.env`.

---

## Common Pitfalls

| Problem | Likely Cause |
|---|---|
| Instagram OAuth fails | App not in Live mode, or redirect URI mismatch in Meta settings |
| `decrypt_token` raises an error | `ENCRYPTION_KEY` changed, or token was saved without encryption |
| WhatsApp webhook not received | Webhook URL not verified, or not subscribed to `messages` field |
| Scheduler doesn't fire for a user | User's `scheduler_active = false`, or `whatsapp_number` is null |
| Images fail to upload | Cloudinary upload preset doesn't exist or isn't set to unsigned |
| Insights API returns empty | Insights take 24h to populate — data is not available immediately after posting |
| `supabase.auth.get_user()` fails | Token expired, or using the wrong Supabase anon key |
| Analytics jobs not running | Scheduler not started (check `startup` logs), or all jobs have `status != scheduled` |
| Carousel post fails | Child containers need 30s to process — this wait is built into `post_carousel()` |
