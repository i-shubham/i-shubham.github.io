# Plugg — Influencer × Brand Marketplace

A static, fully responsive marketplace where **brands post campaigns** and
**creators bid** to collaborate. The frontend data layer (`js/api.js`) connects
to a **Python FastAPI + PostgreSQL** backend with **no UI rewrites** required.

> Part of the GitHub Pages site. Served as a static folder — open
> `digital-marketing/index.html` directly or via any static host.

---

## ✨ What it does


| Role                     | Capabilities                                                                                                                                                                                                                                                                                |
| ------------------------ | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **Creator (Influencer)** | **Connect Instagram/YouTube links** — stats (followers, subscribers, top reel/video views, engagement) are **auto‑fetched and read‑only** (never typed by hand). 30‑day free trial, browse & **bid** on campaigns, see **brief unlocked only after approval**, manage subscription/billing. |
| **Brand**                | Post products/campaigns (title, budget, deliverables, deadline), **see all bidders** side‑by‑side with audience stats, **approve a bid** (auto‑declines others + charges commission), then **share the private video concept**, view commission history, discover creators.                 |
| **Admin**                | Revenue dashboard (brand commission + creator subscriptions + creator commission), user management, **fee levers** (trial length, commission %, subscription price), demo‑data export/reset.                                                                                                |


### Revenue model (built in)

- **Creators:** 30‑day free trial → **Creator Pro** monthly subscription **or** pay‑per‑deal commission.
- **Brands:** small **% commission charged only on an accepted bid**.
- Admin controls every lever from the dashboard (`Fee settings`).

---

## 🗂️ Project structure

```
digital-marketing/
├── index.html                 Landing page (dual creator/brand CTA)
├── how-it-works.html          Full flow for both sides
├── pricing.html               Creator & brand pricing
├── login.html / register.html Auth with role selector
├── marketplace.html           Public campaign browser
├── influencers.html           Public creator directory
├── dashboard-influencer.html  Creator app shell  -> js/influencer.js
├── dashboard-brand.html       Brand app shell     -> js/brand.js
├── dashboard-admin.html       Admin app shell     -> js/admin.js
├── css/styles.css             Design system (responsive, mobile‑first)
└── js/
    ├── api.js     ★ single data/API layer (localStorage now, REST later)
    ├── seed.js    demo data (creators, brands, campaigns, bids)
    ├── app.js     shared shell: nav, footer, toast, modal, helpers, guards
    ├── influencer.js / brand.js / admin.js   per‑role dashboard logic
```

---

## 🔌 Running the FastAPI backend

**All data access is funneled through `js/api.js`.** The UI never touches
storage directly.

```bash
cd backend
make migrate-up        # create tables (first time only)
make seed              # populate demo data
make run               # start server on http://localhost:8080
```

The server serves the frontend at `/` and all API routes at `/api/*`.

In `js/api.js` the backend is already enabled:
```js
API.state.useBackend = true;
API.state.baseURL = "/api";
```

### Suggested REST endpoints


| UI method          | Method & path                                                     |
| ------------------ | ----------------------------------------------------------------- |
| `register`         | `POST /auth/register`                                             |
| `login`            | `POST /auth/login` → `{ token, user }`                            |
| `currentUser`      | `GET /me`                                                         |
| `listProducts`     | `GET /products`                                                   |
| `createProduct`    | `POST /products`                                                  |
| `bidsForProduct`   | `GET /products/{id}/bids`                                         |
| `placeBid`         | `POST /products/{id}/bids`                                        |
| `updateBidStatus`  | `PATCH /bids/{id}`                                                |
| `shareConcept`     | `POST /bids/{id}/concept`                                         |
| `getConceptForBid` | `GET /bids/{id}/concept`                                          |
| `listInfluencers`  | `GET /influencers`                                                |
| `connectSocial`    | `POST /influencers/{id}/connect`                                  |
| `syncStats`        | `POST /influencers/{id}/sync` (calls IG Graph / YouTube Data API) |
| `subscribe`        | `POST /subscriptions`                                             |
| `recordPayment`    | `POST /payments`                                                  |
| `adminRevenue`     | `GET /admin/revenue`                                              |


### PostgreSQL schema

```sql
users(id BIGSERIAL, role CHECK IN ('influencer','brand','admin'), name, email UNIQUE, password_hash, created_at)
influencer_profiles(user_id FK, handle, niche, bio, location,
  insta_url, yt_url, last_synced,
  insta_followers, insta_top_reel, yt_subscribers, yt_top_views, engagement,
  trial_start, plan, plan_type, subscribed_until)
brand_profiles(user_id FK, company, industry, website, about, logo)
products(id, brand_user_id FK, title, description, category, budget,
  deadline, deliverables, status, created_at)
bids(id, product_id FK, influencer_user_id FK, amount, message, status, created_at)
concepts(id, bid_id FK, product_id FK, brand_user_id FK, influencer_user_id FK,
  concept TEXT, script TEXT, deliverables, deadline, shared_at)
payments(id, type, user_id FK, ref_id, gross, amount, status, note, created_at)
```

### Backend stack

- **Python 3.10+** with **FastAPI** (async, auto-generated OpenAPI docs at `/docs`)
- **SQLAlchemy 2** ORM + **psycopg2** driver
- **PostgreSQL 18** (local) or any managed Postgres (Supabase, Neon, RDS)
- **JWT** auth via `python-jose` (`Authorization: Bearer …` — `api.js` already sends it)
- **Migrations:** raw SQL in `migrations/` — apply with `make migrate-up`
- **Payments:** Razorpay / Stripe — replace the demo checkout modals; on
webhook success call `POST /api/subscriptions` or `POST /api/payments`.

### Why FastAPI?

- **Pythonic & fast to iterate:** clean async syntax, type hints everywhere.
- **Auto OpenAPI docs:** visit `http://localhost:8080/docs` for interactive Swagger UI.
- **Pydantic v2 validation:** request/response schemas are validated automatically.
- **Easy deployment:** Docker, Render, Railway, Fly.io — all first-class supported.
- **Large ecosystem:** SQLAlchemy, Alembic, Celery, and the full PyPI library catalog.

---

## 🧪 Try the demo

Open `index.html`. The app seeds realistic data on first load.


| Role    | Email                  | Password   |
| ------- | ---------------------- | ---------- |
| Creator | `aaravcreates@demo.io` | `demo123`  |
| Brand   | `nimbusaudio@demo.io`  | `demo123`  |
| Admin   | `admin@plugg.io`       | `admin123` |


Reset anytime from **Admin → Demo data → Reset**.

---

## 📱 Responsive & robust

- Mobile‑first CSS, collapsible nav + dashboard drawer, touch‑friendly targets.
- Works on any modern mobile or desktop browser; no build step, no dependencies.
- Input validation, duplicate‑bid/email guards, role‑based route protection,
and HTML‑escaping throughout.

