<div align="center">

# ⚖️ Nyaya-ZTA

### Zero Trust Explainable AI Framework for Secure Judicial Decision Support

[![CI](https://github.com/your-username/nyaya-zta/actions/workflows/ci.yml/badge.svg)](https://github.com/your-username/nyaya-zta/actions/workflows/ci.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://python.org)
[![Next.js 15](https://img.shields.io/badge/Next.js-15-black.svg)](https://nextjs.org)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.115+-009688.svg)](https://fastapi.tiangolo.com)
[![SQLite3](https://img.shields.io/badge/Database-SQLite3-003B57.svg)](https://sqlite.org)

*A production-quality research prototype combining Zero Trust Architecture, Explainable AI, RAG, and tamper-evident audit ledger for judicial decision support systems.*

</div>

---

## 📋 Table of Contents

- [Overview](#overview)
- [Key Features](#key-features)
- [Architecture](#architecture)
- [Tech Stack](#tech-stack)
- [Quick Start](#quick-start)
- [Database Management (SQLite & PostgreSQL)](#database-management-sqlite--postgresql)
- [Project Structure](#project-structure)
- [Configuration](#configuration)
- [Deployment](#deployment)
- [Research Contributions](#research-contributions)
- [Testing](#testing)
- [Documentation](#documentation)
- [License](#license)

---

## Overview

**Nyaya-ZTA** (Sanskrit: *Nyaya* = Justice) is a research framework that demonstrates how modern AI systems can be integrated into judicial decision support while maintaining:

1. **Zero Trust Security** — Every request is continuously verified; no implicit trust
2. **Explainable AI** — All AI recommendations include SHAP-based explanations
3. **Retrieval-Augmented Generation** — Grounded in actual legal documents with citation support
4. **Tamper-Evident Audit Trail** — Blockchain-inspired ledger with Merkle trees and digital signatures
5. **Offline & Self-Contained Database** — Uses SQLite3 out of the box with zero external database dependencies
6. **Provider-Independent LLM** — Works with any OpenAI-compatible API (Groq, OpenAI, Anthropic, local models)

The framework is **jurisdiction-agnostic** by design, with configurable legal categories, court hierarchies, and applicable statutes. The prototype ships with synthetic Indian judicial data for demonstration.

> **⚠️ Research Prototype Notice**: This software is designed for research purposes and academic publication. It has not undergone the regulatory approval process required for production use in actual judicial proceedings.

---

## Key Features

### 🔐 Zero Trust Architecture
- Continuous identity verification on every request
- Device trust assessment and fingerprinting
- Context-aware access control (RBAC + ABAC hybrid)
- Policy Decision Point with real-time evaluation
- All access decisions logged to immutable audit ledger

### 🧠 AI-Powered Judicial Support
- **Case Summarization** — Automated case analysis and summary generation
- **Risk Assessment** — ML-based risk scoring with feature importance
- **Judgment Assistance** — RAG-powered legal research and analysis
- **Bias Detection** — Framework for detecting and reporting model bias
- **Human-in-the-Loop** — All AI recommendations require judge approval

### 📊 Explainable AI
- SHAP (SHapley Additive exPlanations) integration
- Feature importance visualization
- Natural language explanations of AI decisions
- Trust and confidence scoring with transparency

### 📄 RAG Pipeline
- Document upload and chunking
- Embedding generation (Sentence-BERT)
- FAISS vector search
- Context-aware prompt building
- Citation tracking and verification

### 🔗 Tamper-Evident Audit Ledger
- SHA-256 hash chaining
- Merkle tree integrity verification
- ECDSA digital signatures
- Inclusion proofs
- Full chain verification

### 👥 Role-Based Portals
- **Citizen Portal** — File cases, upload documents, track status
- **Lawyer Portal** — Manage cases, legal research, document management
- **Judge Dashboard** — AI-assisted review, explainability, approve/reject
- **Admin Dashboard** — User management, policies, system audit

---

## Architecture

```
┌──────────────────────────────────────────────────────────────────┐
│                    Frontend (Next.js 15)                         │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────────────┐   │
│  │ Citizen   │ │ Lawyer   │ │ Judge    │ │ Admin Dashboard  │   │
│  │ Portal    │ │ Portal   │ │ Dashboard│ │                  │   │
│  └──────────┘ └──────────┘ └──────────┘ └──────────────────┘   │
│                  ShadCN UI + TailwindCSS                        │
└──────────────────────────┬───────────────────────────────────────┘
                           │ HTTPS + JWT
┌──────────────────────────┴───────────────────────────────────────┐
│                   Backend (FastAPI)                               │
│  ┌─────────┐ ┌────────────┐ ┌──────────┐ ┌──────────────────┐  │
│  │ Auth &   │ │ Case       │ │ AI       │ │ RAG Pipeline     │  │
│  │ Zero     │ │ Management │ │ Engine & │ │ (FAISS + LLM)    │  │
│  │ Trust    │ │            │ │ SHAP     │ │                  │  │
│  └─────────┘ └────────────┘ └──────────┘ └──────────────────┘  │
│  ┌─────────┐ ┌────────────┐ ┌──────────────────────────────┐   │
│  │ Policy   │ │ Evidence   │ │ Audit Ledger                 │   │
│  │ Engine   │ │ Verify     │ │ (Hash Chain + Merkle Tree)   │   │
│  └─────────┘ └────────────┘ └──────────────────────────────┘   │
└──────────────────────────┬───────────────────────────────────────┘
                           │
        ┌──────────────────┼──────────────────┐
        │                  │                  │
┌───────┴───────┐ ┌───────┴────────┐ ┌──────┴───────┐
│ SQLite3       │ │ Local Files    │ │ Groq API     │
│ (nyaya.db)    │ │ (/uploads/)    │ │ (LLM)        │
└───────────────┘ └────────────────┘ └──────────────┘
```

---

## Tech Stack

| Layer | Technology |
|-------|-----------|
| Frontend | Next.js 15, React 19, TypeScript, TailwindCSS v4, ShadCN UI |
| Backend | FastAPI, Python 3.11+, SQLAlchemy 2.x (async), Pydantic |
| Database | SQLite3 (via `aiosqlite`) — PostgreSQL ready |
| Auth | Custom JWT (`python-jose` + `bcrypt`) with access/refresh tokens |
| Storage | Local filesystem (`/backend/uploads/`) with SHA-256 integrity |
| Vector DB | FAISS (`faiss-cpu`) |
| Embeddings | Sentence-Transformers (`all-MiniLM-L6-v2`) |
| ML | Scikit-learn, PyTorch, SHAP |
| LLM | Provider-independent (Groq API for prototype) |
| Audit | SHA-256, Merkle Tree, ECDSA (P-256) |
| Deployment | Docker, Docker Compose, Vercel, Render |
| CI/CD | GitHub Actions |

---

## Quick Start

### Prerequisites

- Python 3.11+
- Node.js 20+
- Docker & Docker Compose (optional)
- A [Groq](https://console.groq.com) API key (free tier, for LLM capabilities)

### 1. Clone the Repository

```bash
git clone https://github.com/your-username/nyaya-zta.git
cd nyaya-zta
```

### 2. Configure Environment Variables

```bash
# Backend
cp backend/.env.example backend/.env

# Frontend
cp frontend/.env.example frontend/.env.local
```

### 3a. Run with Docker Compose (Recommended)

```bash
docker-compose up --build
```

The application will be available at:
- Frontend: http://localhost:3000
- Backend API: http://localhost:8000
- API Docs: http://localhost:8000/docs

### 3b. Run Without Docker

**Backend:**
```bash
cd backend
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt
alembic upgrade head
uvicorn app.main:app --reload --port 8000
```

**Frontend:**
```bash
cd frontend
npm install
npm run dev
```

---

## Database Management (SQLite & PostgreSQL)

### How SQLite Works in Nyaya-ZTA

By default, Nyaya-ZTA uses an embedded SQLite database configured for high performance:
- **Location**: `backend/database/nyaya.db` (automatically created on first run)
- **Driver**: `aiosqlite` via SQLAlchemy 2.x async engine
- **PRAGMAs**: Configured with Write-Ahead Logging (WAL mode), foreign key constraints enabled, and optimized page cache.
- **Portability**: All primary keys are stored as standard `String(36)` UUIDs and metadata as standard `JSON`, ensuring 100% portability with PostgreSQL.

### Backing Up the Database

Since SQLite is a single self-contained file, backups are simple:

```bash
# Method 1: File copy (safe when WAL mode is used)
cp backend/database/nyaya.db backend/database/nyaya_backup_$(date +%Y%m%d).db

# Method 2: Online backup using SQLite CLI
sqlite3 backend/database/nyaya.db ".backup 'backend/database/nyaya_backup.db'"
```

### Restoring the Database

To restore from a backup file:

```bash
# 1. Stop backend service
# 2. Replace database file
cp backend/database/nyaya_backup.db backend/database/nyaya.db
# 3. Restart backend service
```

### Migrating to PostgreSQL for Production

Nyaya-ZTA is designed using Clean Architecture and the Repository Pattern. **Zero business logic changes** are required to switch to PostgreSQL.

1. **Install PostgreSQL driver**:
   ```bash
   pip install asyncpg psycopg2-binary
   ```

2. **Update `DATABASE_URL` in `backend/.env`**:
   ```env
   DATABASE_URL=postgresql+asyncpg://postgres:password@localhost:5432/nyaya_db
   ```

3. **Run Alembic Migrations against PostgreSQL**:
   ```bash
   cd backend
   alembic upgrade head
   ```

Everything else continues working seamlessly!

---

## Project Structure

```
nyaya-zta/
├── backend/                # FastAPI Python Backend
│   ├── app/
│   │   ├── core/           # Security (JWT, bcrypt), logging, middleware
│   │   ├── auth/           # Authentication module
│   │   ├── authorization/  # RBAC + ABAC policy engine
│   │   ├── cases/          # Case management
│   │   ├── documents/      # Document upload & management
│   │   ├── evidence/       # Evidence verification
│   │   ├── ai/             # AI recommendation engine
│   │   ├── explainability/ # SHAP, explanations
│   │   ├── rag/            # RAG pipeline (FAISS)
│   │   ├── llm/            # Provider-independent LLM
│   │   ├── ledger/         # Tamper-evident audit ledger
│   │   ├── zero_trust/     # Zero Trust module
│   │   ├── search/         # Full-text + semantic search
│   │   ├── notifications/  # Notification system
│   │   └── db/             # Database layer (engine, base, init_db)
│   ├── database/           # SQLite database directory (nyaya.db)
│   ├── uploads/            # Local document storage
│   ├── tests/              # Unit, integration, security tests
│   ├── research/           # Formal models and algorithms
│   └── alembic/            # Database migrations
├── frontend/               # Next.js Frontend
│   └── src/
│       ├── app/            # App Router pages
│       ├── components/     # Reusable UI components
│       ├── lib/            # Utilities and API client
│       ├── hooks/          # Custom React hooks
│       ├── store/          # State management (Zustand)
│       └── types/          # TypeScript type definitions
├── docs/                   # Documentation
├── docker-compose.yml      # One-command local deployment
└── .github/workflows/      # CI/CD pipelines
```

---

## Configuration

All configuration is managed through environment variables. See:
- [`backend/.env.example`](backend/.env.example) — Backend configuration
- [`frontend/.env.example`](frontend/.env.example) — Frontend configuration

---

## Research Contributions

This framework contributes the following to the research community:

1. **Formal Trust Model** — Mathematical formulation of trust score computation
2. **Hybrid Access Control Model** — Combined RBAC + ABAC for judicial systems
3. **Explainability Framework** — SHAP integration with domain-specific explanation generation
4. **Tamper-Evident Audit Architecture** — Blockchain-inspired ledger without infrastructure overhead
5. **Zero Trust for Judicial AI** — Continuous verification model for sensitive decision support

See [`backend/research/`](backend/research/) for formal models, algorithms, and mathematical formulations.

---

## Testing

```bash
# Backend unit tests
cd backend
python -m pytest tests/unit/ -v --cov=app

# Backend integration tests
python -m pytest tests/integration/ -v

# Backend security tests
python -m pytest tests/security/ -v

# Frontend type check
cd frontend
npx tsc --noEmit

# Frontend lint
npm run lint
```

---

## Documentation

| Document | Description |
|----------|-------------|
| [Installation Guide](docs/INSTALLATION.md) | Step-by-step setup instructions |
| [Developer Guide](docs/DEVELOPER_GUIDE.md) | Architecture, patterns, contributing |
| [API Documentation](docs/API_DOCUMENTATION.md) | REST API reference |
| [Architecture](docs/ARCHITECTURE.md) | System design and diagrams |
| [Deployment Guide](docs/DEPLOYMENT.md) | Production deployment instructions |

---

## License

This project is licensed under the MIT License — see the [LICENSE](LICENSE) file for details.

---

<div align="center">
<i>Built for research. Designed for publication. Engineered for production.</i>
</div>
