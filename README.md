# Smart Procurement System

An AI-powered procurement and clinic-operations platform for Ayurvedic clinics, featuring an AI assistant that answers natural-language questions grounded in live clinic data.

## Live Demo

**URL:** https://smart-procurement-system-devs-projects-27a2efa5.vercel.app

**Demo login:** username `doctor_1` / password `doctor123`

> The backend runs on Render's free tier and spins down after 15 minutes of inactivity. The first request after idle may take **30–60 seconds** to wake up. Subsequent requests are fast.

---

## Screenshots

| Dashboard | AI Assistant |
|-----------|-------------|
| *(screenshot)* | *(screenshot)* |

---

## Key Features

- **AI Assistant** — Ask questions in plain English: *"Which medicines are low in stock?"*, *"What was today's revenue?"*, *"How many pending purchase orders?"*. In production the assistant uses Groq (llama-3.1-8b-instant) for natural-language responses with live DB context injected per query. In mock mode (no API key required) the same DB queries run and results are returned directly — no LLM call, no torch dependency.
- **Role-based access** — Five roles: `admin`, `doctor`, `pharmacist`, `receptionist`, `therapist`. Each role sees only the actions and data relevant to it.
- **Inventory management** — Medicine catalog with real-time low-stock alerts (configurable threshold) and expiry warnings (30-day critical / 90-day advance notice). Dashboard stats update on every page load.
- **Procurement workflow** — Full purchase-order lifecycle: draft → approved → ordered → received. Approval gated to doctor/admin; orders under ₹5,000 are auto-approvable.
- **Billing** — Bill generation tied to patient visits; today's and monthly revenue surfaced on the dashboard.
- **Patient records & appointments** — Patient profiles, visit history, appointment scheduling, and today's appointment count on the dashboard.
- **Reporting dashboard** — Revenue breakdown charts (Recharts), inventory summary, and procurement status at a glance.

---

## Tech Stack

| Layer | Technologies |
|-------|-------------|
| **Backend** | FastAPI 0.104, Python 3.11, SQLAlchemy 2.0 ORM, Alembic, Uvicorn |
| **Database** | PostgreSQL (Neon serverless in production; local PostgreSQL in dev) |
| **Auth** | JWT via python-jose, bcrypt password hashing, Bearer-token headers |
| **AI** | Groq API (llama-3.1-8b-instant), FAISS-cpu, Sentence Transformers (all-MiniLM-L6-v2) |
| **Frontend** | React 19, Vite 7, React Router 7, Recharts 3, Axios, Lucide React |
| **Deployment** | Render (backend), Vercel (frontend), Neon (database) |

---

## Architecture

```
React (Vercel)
    │  HTTPS / Bearer token
    ▼
FastAPI (Render)
    ├── /api/v1/auth          JWT issue & verify
    ├── /api/v1/inventory     InventoryStock model
    ├── /api/v1/procurement   PurchaseOrder model
    ├── /api/v1/billing       Bill model
    ├── /api/v1/patients      Patient / Appointment models
    ├── /api/v1/reports       aggregated SQL queries
    └── /api/v1/chatbot/chat
            │
            ▼
        ChatbotEngine  (backend/ai/chatbot_engine.py)
            ├── classify_intent()   LLMService (Groq) or MockLLMService
            ├── _get_db_context()   direct SQLAlchemy queries (no torch/FAISS at runtime)
            └── generate_response() LLMService with DB context injected as system message
    │
    ▼
PostgreSQL (Neon)
    users · patients · medicines · inventory_stock
    vendors · purchase_orders · purchase_order_items
    appointments · bills · bill_items · chat_conversations
```

> **RAG note:** The full FAISS + Sentence Transformers pipeline (`backend/ai/rag_pipeline.py`, `backend/ai/embeddings.py`) is implemented but disabled at runtime on Render's free tier (512 MB RAM; torch alone needs ~2 GB). Both mock and Groq modes use direct DB queries for context instead, which is faster and more accurate for structured data anyway.

---

## Local Setup

### Prerequisites

- Python 3.11+
- Node.js 18+
- PostgreSQL 14+ (local) **or** a [Neon](https://neon.tech) free-tier connection string

### 1. Clone and configure

```bash
git clone https://github.com/<your-username>/smart-procurement-system.git
cd smart-procurement-system
cp .env.example .env
# Edit .env and fill in the required values (see comments inside)
```

### 2. Backend

```bash
python -m venv venv

# Windows
venv\Scripts\activate
# macOS / Linux
source venv/bin/activate

pip install -r requirements.txt

# Start the API server (from the repo root)
uvicorn backend.main:app --reload --port 8000
```

The app auto-creates all database tables on first startup via SQLAlchemy.
API docs: http://localhost:8000/api/v1/docs

### 3. Seed demo data

Run once after tables are created:

```bash
python scripts/seed_demo_data.py
```

Creates ~40 medicines, ~8 vendors, purchase orders, patients, appointments, and bills with realistic data. Safe to re-run — catalog data is skipped if already present; time-sensitive data (today's appointments/bills) is always topped up.

**Default demo accounts:**

| Username | Password | Role |
|----------|----------|------|
| `admin_1` | `admin123` | Admin |
| `doctor_1` | `doctor123` | Doctor |
| `pharmacist_1` | `pharm123` | Pharmacist |
| `receptionist_1` | `recept123` | Receptionist |
| `therapist_1` | `therap123` | Therapist |

### 4. Frontend

```bash
cd frontend
npm install

# Point the frontend at your local backend
echo "VITE_API_URL=http://localhost:8000/api/v1" > .env.local

npm run dev
```

Frontend: http://localhost:5173

---

## Environment Variables

Copy `.env.example` to `.env` and fill in the values. All required variables are marked.

### Keyless local runs (mock mode)

Set `USE_MOCK_LLM=true` in `.env`. The chatbot will answer questions using live DB data without calling Groq. Intent classification uses keyword matching; responses are the raw DB query results formatted as plain text. No Groq API key is needed in this mode.

---

## Deployment

### Backend — Render

**Build command:** `pip install -r requirements.txt`  
**Start command:** `uvicorn backend.main:app --host 0.0.0.0 --port $PORT`

Required environment variables:

| Variable | Description |
|----------|-------------|
| `DATABASE_URL` | Neon connection string (`postgresql://...?sslmode=require`) |
| `SECRET_KEY` | Long random string for JWT signing |
| `GROQ_API_KEY` | Groq API key — **or** set `USE_MOCK_LLM=true` to skip |
| `USE_MOCK_LLM` | `true` to disable Groq and use mock responses |
| `ENVIRONMENT` | `production` |
| `DEBUG` | `false` |

### Frontend — Vercel

| Variable | Value |
|----------|-------|
| `VITE_API_URL` | `https://<your-render-service>.onrender.com/api/v1` |

`VITE_API_URL` is baked into the JS bundle at build time. If the Render URL ever changes, redeploy the frontend too.

### Keep Render warm (optional)

Use [UptimeRobot](https://uptimerobot.com) (free) to ping `https://<render-url>/health` every 5 minutes so the instance doesn't spin down between visits.

---

## Project Structure

```
smart-procurement-system/
├── backend/
│   ├── ai/
│   │   ├── chatbot_engine.py   orchestrates intent → context → response
│   │   ├── llm_service.py      Groq client + MockLLMService
│   │   ├── rag_pipeline.py     FAISS RAG (local use only)
│   │   └── embeddings.py       Sentence Transformers wrapper
│   ├── api/routes/             11 route modules (auth, inventory, chatbot, …)
│   ├── auth/security.py        JWT helpers
│   ├── config/
│   │   ├── settings.py         pydantic-settings config
│   │   └── database.py         SQLAlchemy engine + session
│   ├── models/database.py      all ORM models
│   ├── schemas/schemas.py      Pydantic request/response schemas
│   └── main.py                 FastAPI app + middleware + startup
├── frontend/
│   └── src/
│       ├── contexts/AuthContext.jsx
│       ├── pages/              Dashboard, Inventory, Chatbot, …
│       ├── services/api.js     Axios instance + all API calls
│       └── App.jsx
├── scripts/
│   └── seed_demo_data.py       single-command demo data seed
├── .env.example
├── requirements.txt
└── README.md
```

---

## Known Limitations / Roadmap

- **RAG disabled on free tier** — FAISS + Sentence Transformers is fully implemented but not loaded at runtime on Render (torch exceeds the 512 MB RAM limit). It works fine locally. Upgrading to a paid Render instance (1 GB+) or a separate embedding service would re-enable it.
- **Mock chatbot responses are minimal** — In mock mode the chatbot returns the raw DB count/sum result without any rephrasing. Switching to `USE_MOCK_LLM=false` with a Groq key gives natural-language answers and comparisons.
- **Reports page is partial** — Revenue and inventory charts render correctly; vendor-performance and treatment-analytics sections are wired in the backend but not yet surfaced in the UI.
- **File uploads are ephemeral on Render** — The upload path is configured but Render's filesystem resets on each deploy. S3 or Cloudflare R2 integration is the right next step.
- **WhatsApp notifications** — `notification_service.py` skeleton exists; the WhatsApp API integration is not implemented.
- **Forecasting** — Demand forecasting was planned with a time-series model but is not implemented; tensorflow is removed from the dependency list.
