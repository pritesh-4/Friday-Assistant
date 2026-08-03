# 🤖 F.R.I.D.A.Y.

### **Future Responsive Intelligent Digital Assistant for You**

> _"Sometimes the best interface is a conversation."_

F.R.I.D.A.Y. is an ambitious explore-and-build project aiming to create a personal AI operating layer—a companion that understands context, remembers interactions, and assists with workflows.

This repository contains both the **React Frontend** (directly at the root level) and a **FastAPI Python Backend** (in the `backend/` directory) representing a prototype system.

---

## 📖 Summary of Vision & Inspiration

### 🌌 The Inspiration

Inspired by Tony Stark's relationship with J.A.R.V.I.S. and F.R.I.D.A.Y. in sci-fi, this project explores how close modern LLMs, voice recognition, and agentic memory can bring us to a truly personal companion. Rather than multiple tabs and manual window shifting, the goal is a conversational interface that handles digital interactions behind the scenes.

### 🎯 Core Vision & Boundaries

- **What F.R.I.D.A.Y. aims to be**: A highly personalized AI assistant, voice-first companion, long-term memory system, and computer task orchestrator.
- **Current Real-world Boundaries**: While movie-style consciousness, general intelligence (AGI), and perfect reasoning are not currently possible, we can utilize state-of-the-art LLMs, multi-agent frameworks, and vector-store memory to implement advanced assistive capabilities.

---

## 🛠️ Technology Stack

### 💻 Frontend

- **Framework**: React 19 + Vite 8
- **Routing**: React Router DOM v7 (SPA architecture)
- **Styling**: Tailwind CSS v4 (using the `@tailwindcss/vite` plugin)
- **Animations**: Framer Motion for smooth, high-fidelity UI transitions
- **Icons**: Lucide React
- **Background Visuals**: HTML5 Canvas with custom WebGL shaders for the ambient cyber-grid effect

### 🐍 Backend

- **Framework**: FastAPI (Python 3.x)
- **Server**: Uvicorn
- **Settings & Validation**: Pydantic v2
- **Vector Search**: ChromaDB (semantic memory layer)
- **Environment Management**: python-dotenv

---

## 📂 Project Directory Structure

```text
Friday/                          # Project Root (React Frontend)
├── src/                         # React Frontend Source
│   ├── assets/                  # Images, fonts, and styling assets
│   ├── components/              # Reusable UI components (Orb, ShaderBackground, ChatWindow, etc.)
│   ├── pages/                   # Main Page Views (Home, Chat, Vision, About)
│   ├── services/                # API communication layers (chatService, memoryService, etc.)
│   ├── App.jsx                  # React Router routes setup
│   ├── main.jsx                 # Application entrypoint
│   └── index.css                # Global styles, fonts, and Tailwind directives
├── public/                      # Static assets for frontend
├── backend/                     # Python FastAPI Backend
│   ├── app/
│   │   ├── agents/              # AI agent definitions (router, base, memory, planner, web research)
│   │   ├── api/                 # API Routes and dependencies (chat, voice, planning, background, etc.)
│   │   ├── core/                # Core configuration, constants, logging, and security
│   │   ├── db/                  # SQLite persistence & initialization
│   │   ├── identity/            # Identity Engine (canonical entity registry and validation)
│   │   ├── intent/              # Intent Engine (query classification, risk analyzer)
│   │   ├── knowledge_graph/     # Knowledge Graph Engine (node/edge traversals, pathfinding)
│   │   ├── memory/              # Cognitive Memory Engine V2 (CME consolidator, conflict resolution)
│   │   ├── planning/            # Executive Planner (Goal decomposition DAG scheduler)
│   │   ├── ranking/             # Context scoring and ranking
│   │   ├── schemas/             # Pydantic models (chat, common, planning, background)
│   │   ├── services/            # Core services (LLM providers, voice, jobs, notifications)
│   │   ├── tools/               # External execution tools (web search, python execution)
│   │   └── main.py              # App initialization, CORS, WebSocket stream mount
│   ├── tests/                   # Backend Pytest suite
│   ├── requirements.txt         # Backend Python dependencies
│   ├── requirements-voice.txt   # Optional voice models dependencies (Whisper, ONNX)
│   └── .env.example             # Example environment variables
├── docs/                        # Complete project documentation system
├── package.json                 # Node package configuration
├── vite.config.js               # Vite compilation mappings
└── README.md                    # This documentation file
```

---

## ✨ Advanced Implemented Features

1. **Dynamic Interactive Core (`Orb.jsx`)**: Renders the central glowing core of F.R.I.D.A.Y. utilizing Framer Motion. The Orb morphs dynamically between states:
   - `idle`: Smooth breathing animation.
   - `listening`: Reactive scale ripples pulsing outwards.
   - `processing`: High-speed orbital rotation.
   - `speaking`: Fluid expanding waves indicating voice output.
2. **Cyberspace Background (`ShaderBackground.jsx`)**: Utilizes custom WebGL fragment shaders on an HTML5 canvas to render a glowing grid background that reacts to window resizing and user interactions.
3. **Full-Duplex Conversational Voice Stream**: A WebSocket-driven voice interaction loop supporting:
   - **Speculative Rolling Speech-to-Text**: Pre-transcribes streaming raw audio chunks (16kHz PCM float32) using `faster-whisper` (`distil-large-v3`) every 800ms.
   - **Barge-in / Interruption Detection**: Allows the user to interrupt the assistant's speech/generation mid-sentence; immediately halts LLM text/TTS generation.
   - **Speculative Memory Prefetching**: Predicts query intent and prefetches relevant long-term context prior to final turn execution.
   - **Text-to-Speech (TTS)**: Powered locally by `kokoro-onnx` for high-quality voice synthesis.
4. **Executive Planner & Goal DAGs**: 
   - **Intent Engine**: Parses user input, analyzes risks, and determines routing strategy.
   - **Goal Analyzer**: Decomposes complex directives into Milestones and tasks structured as a Directed Acyclic Graph (DAG) with dependencies.
   - **Execution Scheduler**: Automatically schedules, evaluates, and updates task execution states, processing independent tasks in parallel.
5. **Cognitive Memory Engine (CME) V2**:
   - Implements a multi-layered memory architecture (short-term conversation history, semantic working memory, and long-term vector store index in ChromaDB).
   - **Consolidator & Conflict Resolver**: Monitors and merges duplicate memories in the background, resolving contradictions based on confidence scores and chronological priority.
6. **Identity Engine & Registry**:
   - Manages entity resolution (disambiguating nodes like People, Projects, AI Models, Locations, and Frameworks).
   - Resolves entity aliases, registers new identities, and creates comprehensive user and entity profiles with validation, confidence scoring, and full audit logs.
7. **Knowledge Graph Context Engine**:
   - Captures rich semantic links between entities using nodes and directed relationships.
   - Implements BFS traversal, neighborhood expansion, shortest-path calculation, transitive reasoning chains, and hybrid search.
   - Generates natural language explanations of connections between concepts.
8. **Background Job Worker**:
   - Offloads long-running processes (e.g. model downloads, web research) into an asynchronous background queue, reporting status and dispatching readable notifications to the client UI.

---

## ⚡ Getting Started

### 🖥️ Frontend Setup

To run the React dashboard locally:

```bash
# Install dependencies
npm install

# Start local Vite development server (usually runs on http://localhost:5173)
npm run dev
```

To compile a production build:

```bash
npm run build
npm run preview
```

### 🐍 Backend Setup

To run the FastAPI server locally:

```bash
# Navigate to the backend directory
cd backend

# Create a virtual environment
python -m venv venv

# Activate the virtual environment
# On Windows (PowerShell):
venv\Scripts\Activate.ps1
# On macOS/Linux:
source venv/bin/activate

# Install base dependencies
pip install -r requirements.txt

# (Optional) Install Voice dependencies (STT/TTS models)
pip install -r requirements-voice.txt
# Set VOICE_ENABLED=true in your .env file to activate the models locally

# Start the uvicorn web server (runs on http://127.0.0.1:8000)
uvicorn app.main:app --reload
```

Interactive API docs are available at `http://127.0.0.1:8000/docs`.

### 🐳 Docker Deployment (Recommended)

You can easily run the entire F.R.I.D.A.Y. stack (Frontend and Backend) using Docker Compose:

```bash
# Start all services
docker-compose up -d --build

# View logs
docker-compose logs -f

# Stop all services
docker-compose down
```

The frontend will be available on `http://localhost:80` and the backend on `http://localhost:8000`.

## Author

Pritesh Jena [[pritesh-4](https://github.com/pritesh-4)]
