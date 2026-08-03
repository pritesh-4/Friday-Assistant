# PROJECT_STRUCTURE

> **Purpose**: Document every folder in the repository.
> **Scope**: Entire repository.
> **Last Updated**: 2026-08-03
> **Related Documents**: [FRONTEND_ARCHITECTURE.md](./FRONTEND_ARCHITECTURE.md), [BACKEND_ARCHITECTURE.md](./BACKEND_ARCHITECTURE.md)

## Quick Summary
A comprehensive map of the project directory structure.

---

## Root Layout
The React frontend configuration and files are placed directly in the repository root directory. The FastAPI backend is isolated in the `/backend` subdirectory.

```text
/                                # React Frontend Project Root
├── src/                         # React Frontend Source
│   ├── assets/                  # Static assets (images, logos, styles)
│   ├── components/              # Reusable React components (Orb, ShaderBackground, ChatWindow, Sidebar)
│   ├── context/                 # React state provider contexts (Theme, etc.)
│   ├── pages/                   # Top-level page views (Home, Chat, Vision, About)
│   ├── services/                # Backend API REST & WebSocket stream wrappers
│   ├── App.jsx                  # Main router and component layout setup
│   ├── main.jsx                 # Vite application entrypoint
│   └── index.css                # Global Tailwind CSS v4 directives
├── public/                      # Public static files
├── backend/                     # Python FastAPI server project folder
└── docs/                        # Project documentation (this folder)
```

## Frontend Structure (`/`)

```text
src/
├── assets/       # Static assets (sounds, logos, custom cursors)
├── components/   # Modular React items:
│   ├── Orb.jsx                  # Pulse/breathing particle sphere representing FRIDAY's state
│   ├── ShaderBackground.jsx     # WebGL canvas matrix particle visual
│   ├── ChatWindow.jsx           # Frame displaying conversations and inputs
│   └── Sidebar.jsx              # Navigation between views (Notes, Tasks, Chat)
├── pages/        # Router pages:
│   ├── Home.jsx                 # Landing view presenting the interactive Orb
│   ├── Chat.jsx                 # Conversations workspace
│   ├── Vision.jsx               # Goals and roadmap visualizer
│   └── About.jsx                # Inspirational references and boundary details
├── services/     # API Client handlers:
│   ├── chatService.js           # REST chat history actions
│   ├── memoryService.js         # REST memory consolidation endpoints
│   ├── notesService.js          # REST workspace notes operations
│   ├── tasksService.js          # REST task board actions
│   └── voiceService.js          # REST/WebSocket duplex stream handlers
└── index.css     # Global styles containing Tailwind CSS v4 theme directives
```

## Backend Structure (`/backend`)

```text
backend/
├── app/
│   ├── agents/                  # Specialized AI agents:
│   │   ├── base_agent.py        # Abstract agent framework definition
│   │   ├── router_agent.py      # Core agent manager router
│   │   ├── planner_agent.py     # Prompt-based planner
│   │   └── scheduler.py         # Goal DAG scheduler execution agent
│   ├── api/                     
│   │   └── routes/              # FastAPI route controllers:
│   │       ├── voice.py         # Voice services, diagnostics, & WebSocket streams
│   │       ├── planning.py      # Goal decomposition and scheduling endpoints
│   │       ├── background.py    # Background worker job and notifications API
│   │       └── chat.py/memory.py/etc. # REST resource routes
│   ├── core/                    # Configurations, logging settings, rate-limit specs
│   ├── db/                      # SQLite DB initialize script and thread-safe driver
│   ├── identity/                # Entity Registry & profiles resolver engine
│   ├── intent/                  # Intent categorization and safety risk analyzers
│   ├── knowledge_graph/         # Semantic entity-relationship graph traverser
│   ├── memory/                  # CME V2 consolidator and conflict resolving logic
│   ├── planning/                # Goal DAG executive planner pipeline
│   ├── ranking/                 # Cognitive memory scoring and ranker
│   ├── schemas/                 # Pydantic v2 schemas for request/response serialization
│   ├── services/                # External services (LLMProviders gateway, Whisper, Kokoro)
│   ├── tools/                   # Extensible agent tools (web research, code execution)
│   └── main.py                  # API server startup & WebSocket route mapping
├── tests/                       # Pytest verification suites
├── requirements.txt             # Primary application Python packages
└── requirements-voice.txt       # Optional Faster-Whisper & ONNX voice dependencies
```
