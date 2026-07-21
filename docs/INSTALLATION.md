# Nyaya-ZTA — Installation Guide

## Complete Offline Setup Instructions

This guide walks you through setting up Nyaya-ZTA from scratch with zero cloud database or cloud storage dependencies.

---

## Prerequisites

| Tool | Version | Installation |
|------|---------|-------------|
| Python | 3.11+ | [python.org](https://python.org) |
| Node.js | 20+ | [nodejs.org](https://nodejs.org) |
| Git | Latest | [git-scm.com](https://git-scm.com) |
| Docker | Latest (optional) | [docker.com](https://docker.com) |

---

## Step 1: Get an LLM API Key (Optional for basic features)

Nyaya-ZTA supports provider-independent LLMs via any OpenAI-compatible API. For prototype implementation:

1. Go to [console.groq.com](https://console.groq.com) and sign up (free).
2. Navigate to **API Keys** → **Create API Key**.
3. Copy the generated key.

> **Note**: If no LLM key is provided, non-AI features (Auth, Case Management, Zero Trust, Ledger, Evidence verification) will operate fully offline.

---

## Step 2: Clone and Configure

```bash
# Clone the repository
git clone https://github.com/your-username/nyaya-zta.git
cd nyaya-zta

# Configure backend
cp backend/.env.example backend/.env

# Configure frontend
cp frontend/.env.example frontend/.env.local
```

### Backend Configuration (`backend/.env`)

Default SQLite setup (no cloud database required):

```env
APP_NAME=Nyaya-ZTA
ENVIRONMENT=development
DEBUG=true

# Database (SQLite by default)
DATABASE_URL=sqlite+aiosqlite:///database/nyaya.db

# Authentication (JWT Secret)
JWT_SECRET_KEY=generate-a-secure-random-secret-key

# Storage
UPLOAD_DIR=uploads

# LLM Provider (Groq)
LLM_PROVIDER=groq
LLM_BASE_URL=https://api.groq.com/openai/v1
LLM_API_KEY=your-groq-api-key-here
LLM_MODEL=llama-3.3-70b-versatile
```

---

## Step 3: Run the Application

### Option A: Docker Compose (Recommended)

```bash
docker-compose up --build
```

This starts both frontend (port 3000) and backend (port 8000) with volume mounts for the SQLite database (`nyaya.db`) and document uploads (`/uploads/`).

### Option B: Manual Setup

**Backend:**

```bash
cd backend

# Create virtual environment
python -m venv .venv

# Activate (Windows)
.venv\Scripts\activate

# Activate (macOS/Linux)
source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Run database migrations (auto-creates database/nyaya.db)
alembic upgrade head

# Start the server
uvicorn app.main:app --reload --port 8000
```

**Frontend (in a separate terminal):**

```bash
cd frontend

# Install dependencies
npm install

# Start dev server
npm run dev
```

---

## Step 4: Verify Installation

1. **Backend API Docs**: Open [http://localhost:8000/docs](http://localhost:8000/docs)
2. **Frontend**: Open [http://localhost:3000](http://localhost:3000)
3. **Health Check**: `curl http://localhost:8000/health`

Expected response:
```json
{
  "status": "healthy",
  "timestamp": "2026-07-21T00:00:00Z",
  "uptime_seconds": 10.5
}
```

---

## Troubleshooting

### SQLite Database locked or permission error

- Ensure `backend/database/` directory has write permissions.
- WAL mode is enabled automatically. If running across network shares, WAL mode may be unsupported — set `DATABASE_URL` to standard disk path.

### File upload directory missing

- `backend/uploads/` is automatically created on startup. If running in a container, ensure volume permissions allow write access.

### CORS errors in browser

- Ensure `CORS_ORIGINS` in `backend/.env` matches your frontend origin (default `http://localhost:3000`).

### Migrating to PostgreSQL later

- Install `asyncpg`: `pip install asyncpg`
- Update `DATABASE_URL` in `backend/.env` to PostgreSQL connection string.
- Run `alembic upgrade head`. No application code modifications needed!
