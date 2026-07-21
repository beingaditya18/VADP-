# Nyaya-ZTA System Architecture

```mermaid
graph TD
    Client[Next.js 16 + React 19 Frontend] -->|HTTPS / REST API| FastAPI[FastAPI Backend]
    
    subgraph Zero Trust Security Layer
        FastAPI --> Auth[Custom JWT & bcrypt Auth]
        FastAPI --> PDP[Zero Trust ABAC Policy Engine]
    end

    subgraph Data & Storage Abstraction Layer
        FastAPI --> DB[SQLite3 + aiosqlite WAL Database]
        FastAPI --> Storage[Local File Uploads Storage]
        FastAPI --> FAISS[FAISS Vector Index 384-dim]
    end

    subgraph Core Engines
        FastAPI --> Ledger[Tamper-Evident Ledger Engine]
        Ledger --> ECDSA[NIST P-256 Block Signer]
        Ledger --> Merkle[Binary Merkle Tree Engine]
        
        FastAPI --> RAG[RAG Retrieval Pipeline]
        RAG --> Chunker[Sliding Window Chunker]
        RAG --> LLM[Groq / OpenAI / Mock LLM Client]

        FastAPI --> XAI[Explainable AI Engine]
        XAI --> Trust[Formal Trust Scoring Formula]
        XAI --> Risk[Multi-Factor Risk Engine]
        XAI --> SHAP[SHAP Feature Importance]
    end
```

## Database Schema (Clean Architecture Abstraction)
All database interactions use SQLAlchemy 2.x Repository Pattern over SQLite3 (`aiosqlite`). Switching to PostgreSQL requires changing `DATABASE_URL` in `.env`.
