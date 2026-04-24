<div align="center">
  <img src="fna-saas/frontend/public/logo.png" alt="Advora Logo" width="140" />

  <h1>Advora — Your Voice</h1>

  <p><strong>AI-powered Instagram content automation for financial advisors</strong></p>

  <p>
    Advora generates professional finance content daily, sends it to WhatsApp for one-tap approval,
    and publishes it directly to Instagram — fully automated.
  </p>

  <p>
    <img src="https://img.shields.io/badge/Next.js-16-black?style=flat-square&logo=nextdotjs" />
    <img src="https://img.shields.io/badge/FastAPI-0.115-009688?style=flat-square&logo=fastapi" />
    <img src="https://img.shields.io/badge/Supabase-PostgreSQL-3ECF8E?style=flat-square&logo=supabase" />
    <img src="https://img.shields.io/badge/OpenAI-GPT--4o_mini-412991?style=flat-square&logo=openai" />
    <img src="https://img.shields.io/badge/Tailwind_CSS-3.4-38bdf8?style=flat-square&logo=tailwindcss" />
    <img src="https://img.shields.io/badge/TypeScript-5-3178c6?style=flat-square&logo=typescript" />
  </p>
</div>

---

## What is Advora?

Financial advisors spend hours creating social media content that they're too busy to actually post. Advora solves this by fully automating the process:

1. **AI generates** a professional finance post every day (text + image)
2. **WhatsApp delivers** it to the advisor for one-tap approval
3. **Instagram publishes** it automatically on approval
4. **Analytics track** engagement at 24h, 72h, and 7 days
5. **The AI learns** which content performs best for that specific advisor's audience

No scheduling apps. No copywriters. No manual uploads.

---

## Features

| | Feature |
|---|---|
| 🤖 | **AI Content Generation** — GPT-4o-mini writes captions, hooks, and hashtags across 200+ finance topics |
| 🎨 | **AI Image Creation** — DALL-E 3 generates custom post images, hosted on Cloudinary |
| 📱 | **WhatsApp Approval Flow** — interactive approve/regenerate buttons sent daily |
| 📸 | **Instagram Auto-Publishing** — single images and multi-slide carousels via Graph API |
| 📊 | **Engagement Analytics** — impressions, likes, saves, and engagement rate per post |
| 🔁 | **Performance Feedback Loop** — AI adapts content strategy based on what performs best |
| ⏰ | **Per-User Scheduling** — each advisor sets their own daily post time and timezone |
| 🔐 | **Secure OAuth** — Meta OAuth 2.0 for Instagram; encrypted token storage with Fernet |
| 🛡️ | **Row-Level Security** — Supabase RLS ensures users only ever see their own data |
| 📱 | **Mobile-First Dashboard** — responsive UI with bottom tab navigation on mobile |

---

## Tech Stack

### Backend
| Technology | Role |
|---|---|
| **FastAPI** | REST API framework |
| **SQLAlchemy (async)** | ORM with `asyncpg` for PostgreSQL |
| **Supabase** | Auth, database, and row-level security |
| **APScheduler** | Per-user cron jobs (no external queue needed) |
| **OpenAI API** | GPT-4o-mini (text) + DALL-E 3 (images) |
| **Cloudinary** | Image hosting (Instagram requires public HTTPS URLs) |
| **WhatsApp Cloud API** | Sends draft approval messages |
| **Instagram Graph API** | Publishes posts and fetches insights |
| **Fernet (cryptography)** | Symmetric encryption for stored OAuth tokens |
| **structlog** | Structured JSON logging |
| **slowapi** | Rate limiting |

### Frontend
| Technology | Role |
|---|---|
| **Next.js 16** | React framework with App Router |
| **TypeScript** | Type-safe throughout |
| **Tailwind CSS 3** | Utility-first styling with custom Advora brand palette |
| **Recharts** | Analytics charts (area chart, bar chart) |
| **Supabase SSR** | Server-side session management |
| **date-fns** | Date formatting |

### Infrastructure
| Technology | Role |
|---|---|
| **Supabase** | Hosted PostgreSQL + Auth |
| **Cloudinary** | Image CDN |
| **Meta Developer Platform** | Instagram + WhatsApp APIs |

---

## Architecture & Flow

```
┌─────────────────────────────────────────────────────────┐
│                    DAILY AUTOMATION LOOP                  │
│                                                           │
│  APScheduler (CronTrigger per user)                       │
│        │                                                  │
│        ▼                                                  │
│  OpenAI GPT-4o-mini                                       │
│  ┌─────────────────────────────────────────────────────┐ │
│  │  Reads top/worst themes from DB (feedback loop)     │ │
│  │  Selects theme → generates caption + hashtags       │ │
│  └─────────────────────────────────────────────────────┘ │
│        │                                                  │
│        ▼                                                  │
│  WhatsApp Cloud API  ──────────────────────────────────▶  │
│  "Here's today's post. Approve or regenerate?"            │
│                                                           │
│        │ User taps [Approve]                              │
│        ▼                                                  │
│  DALL-E 3 → Cloudinary (image hosting)                   │
│        │                                                  │
│        ▼                                                  │
│  Instagram Graph API → Published to feed                  │
│        │                                                  │
│        ▼                                                  │
│  Analytics jobs scheduled (24h / 72h / 7d)               │
│        │                                                  │
│        ▼                                                  │
│  Insights → DB → Feedback into next generation           │
└─────────────────────────────────────────────────────────┘
```

---

## Project Structure

```
Agent-Advora/
├── fna-saas/
│   ├── backend/                  # FastAPI (Python)
│   │   ├── app/
│   │   │   ├── main.py           # App entry, lifespan, middleware
│   │   │   ├── api/v1/           # REST endpoints
│   │   │   │   ├── users.py      # Profile & settings
│   │   │   │   ├── drafts.py     # Draft list, detail, manual trigger
│   │   │   │   ├── instagram.py  # OAuth connect / callback / status
│   │   │   │   └── webhook.py    # WhatsApp button reply handler
│   │   │   ├── core/
│   │   │   │   ├── config.py     # Pydantic Settings (all env vars)
│   │   │   │   ├── security.py   # Fernet encryption + HMAC verify
│   │   │   │   └── logging.py    # structlog setup
│   │   │   ├── db/
│   │   │   │   ├── database.py   # Async SQLAlchemy engine
│   │   │   │   └── models.py     # ORM models
│   │   │   └── services/
│   │   │       ├── scheduler.py  # APScheduler — daily jobs, analytics, token refresh
│   │   │       ├── content.py    # OpenAI content generation + 200+ themes
│   │   │       ├── image.py      # DALL-E 3 + Cloudinary upload
│   │   │       ├── instagram.py  # Instagram Graph API
│   │   │       └── whatsapp.py   # WhatsApp Cloud API
│   │   ├── requirements.txt
│   │   └── .env.example
│   │
│   ├── frontend/                 # Next.js 16 (TypeScript + Tailwind)
│   │   ├── app/
│   │   │   ├── (auth)/           # Login + Signup pages
│   │   │   └── dashboard/        # Overview, Drafts, Analytics, Connect, Settings
│   │   ├── components/
│   │   │   ├── Logo.tsx          # Advora logo with fallback
│   │   │   ├── DashboardNav.tsx  # Sidebar + mobile drawer + bottom tabs
│   │   │   └── NavIcons.tsx      # SVG icon set
│   │   └── lib/
│   │       ├── api.ts            # Typed API client
│   │       └── supabase.ts       # Supabase browser client
│   │
│   └── supabase/
│       └── migrations/           # 4 ordered migration files
│           ├── 001_initial_schema.sql
│           ├── 002_indexes.sql
│           ├── 003_rls_policies.sql
│           └── 004_functions.sql  # Triggers, feedback loop views
```

---

## Database Schema

```
user_profiles          instagram_connections
─────────────          ─────────────────────
id (= auth.uid)        user_id (FK)
full_name              ig_user_id
company_name           username
whatsapp_number        encrypted_access_token
post_time_hour         token_expires_at
post_time_minute       profile_picture_url
timezone
scheduler_active       drafts
                       ──────
post_results           user_id (FK)
────────────           theme, hook, caption
draft_id (FK)          hashtags, post_type
instagram_post_id      status ──────────────────────────────────────────────────
image_url              ↓  pending → approved → posting → posted
                          └─────→ rejected   └──────────→ image_failed
post_analytics                                            └──────────→ post_failed
──────────────
post_result_id (FK)    analytics_jobs
fetch_stage            ──────────────
impressions            post_result_id (FK)
likes, saves           scheduled_for
engagement_rate        fetch_stage (24h/72h/7d)
                       status
```

---

## Getting Started

### Prerequisites
- Python 3.11+
- Node.js 20+
- A Supabase project
- Meta Developer account (for Instagram + WhatsApp)
- Cloudinary account
- OpenAI API key

### Backend Setup

```bash
cd fna-saas/backend

# Create and activate virtual environment
python -m venv venv
venv\Scripts\activate        # Windows
# source venv/bin/activate   # Mac/Linux

# Install dependencies
pip install -r requirements.txt

# Configure environment
cp .env.example .env
# Fill in all values in .env

# Run the API
uvicorn app.main:app --reload --port 8000
```

API docs: `http://localhost:8000/docs`

### Frontend Setup

```bash
cd fna-saas/frontend

npm install

# Configure environment
cp .env.local.example .env.local
# Add NEXT_PUBLIC_SUPABASE_URL, NEXT_PUBLIC_SUPABASE_ANON_KEY, NEXT_PUBLIC_API_URL

npm run dev
```

App: `http://localhost:3000`

### Database Setup

Run the Supabase migrations in order via the Supabase SQL Editor:

```
supabase/migrations/001_initial_schema.sql
supabase/migrations/002_indexes.sql
supabase/migrations/003_rls_policies.sql
supabase/migrations/004_functions.sql
```

---

## Key Environment Variables

| Variable | Description |
|---|---|
| `SUPABASE_URL` | Supabase project URL |
| `SUPABASE_SERVICE_ROLE_KEY` | Service role key (bypasses RLS — keep secret) |
| `DATABASE_URL` | `postgresql+asyncpg://...` connection string |
| `ENCRYPTION_KEY` | 64-char hex — encrypts stored OAuth tokens |
| `OPENAI_API_KEY` | GPT-4o-mini + DALL-E 3 |
| `CLOUDINARY_*` | Cloud name, API key, API secret |
| `WHATSAPP_*` | Phone number ID, access token, app secret |
| `META_APP_ID / META_APP_SECRET` | Instagram OAuth |
| `META_OAUTH_REDIRECT_URI` | Must match Meta app settings exactly |

See [`backend/.env.example`](fna-saas/backend/.env.example) for the full list.

---

## Dashboard Pages

| Route | Description |
|---|---|
| `/login` | Email/password sign-in with split brand panel |
| `/signup` | Account creation with password strength indicator |
| `/dashboard` | Overview — status cards, recent drafts, quick actions |
| `/dashboard/drafts` | All drafts with status filter, expandable detail, hashtag pills |
| `/dashboard/analytics` | Charts (impressions, engagement rate), top-performing themes |
| `/dashboard/connect` | Instagram account connection + token status |
| `/dashboard/settings` | Profile, WhatsApp number, schedule, daily scheduler toggle |

---

## Design System

The UI uses a custom Advora brand palette built into Tailwind CSS:

| Token | Color | Usage |
|---|---|---|
| `brand-600` | `#7c3aed` (Purple) | Primary buttons, active nav, links |
| `advora-teal` | `#06b6d4` | Gradient accents, highlights |
| `advora-orange` | `#f97316` | Warm accents |
| `advora-pink` | `#ec4899` | Status indicators |
| `navy-800` | `#162147` | Page titles, headings |

Mobile layout: fixed top header + hamburger drawer + bottom tab bar.

---

## Author

**Rajender Gugulothu**

Built with FastAPI, Next.js, OpenAI, and the Meta Graph API.

---

<div align="center">
  <img src="fna-saas/frontend/public/logo.png" alt="Advora" width="60" />
  <p><em>Advora — Your Voice</em></p>
</div>
