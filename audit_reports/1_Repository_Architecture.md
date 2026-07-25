# 1. Repository Architecture

## Overview
F.R.I.D.A.Y. is a full-stack AI Assistant application.
- **Frontend**: React (Vite)
- **Backend**: FastAPI (Python 3.11)
- **Database**: SQLite (SQLAlchemy) + ChromaDB (Vector Store)

## High-Level Tree
\\\	ext
FRIDAY/
├── backend/                  # FastAPI Application
│   ├── app/                  # Application Logic
│   │   ├── agents/           # Agentic execution layer (Router, Context, Planner)
│   │   ├── ai/               # AI wrappers (Whisper STT, Kokoro TTS)
│   │   ├── api/              # API Routes (Chat, Voice, Memory, Planning, Background)
│   │   ├── core/             # Configuration, Logging, Rate Limiting, Middleware
│   │   ├── db/               # SQLite and ChromaDB initializers
│   │   ├── memory/           # Cognitive Memory management
│   │   ├── schemas/          # Pydantic validation models
│   │   ├── services/         # Core business logic (LLM, Document, Planning)
│   │   └── tools/            # Tool Execution Framework
│   ├── chroma_db/            # Persistent Vector Storage
│   └── data/                 # SQLite DB and Uploads
├── docs/                     # Documentation files
├── public/                   # Static public assets
└── src/                      # React Frontend
    ├── assets/               # Images and icons
    ├── components/           # Reusable UI elements (Chat, Navbar, Sidebar, Matrix)
    ├── constants/            # UI configurations
    ├── context/              # React Context Providers
    ├── data/                 # Mock datasets (TARGETED FOR DELETION)
    ├── hooks/                # Custom React Hooks
    ├── pages/                # Page Views (Chat, Vision, Planning, BackgroundOps)
    └── services/             # API Interceptors and Voice State Machines
\\\
