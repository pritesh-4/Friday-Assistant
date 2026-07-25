# 🤖 F.R.I.D.A.Y.

### **Future Responsive Intelligent Digital Assistant for You**

> _"Sometimes the best interface is a conversation."_

F.R.I.D.A.Y. is an ambitious explore-and-build project aiming to create a personal AI operating layer—a companion that understands context, remembers interactions, and assists with workflows.

This repository contains both the **React Frontend** and a **FastAPI Python Backend** representing a prototype system.


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
- **Environment management**: python-dotenv

---

## 📂 Project Directory Structure

```text
Friday/
├── backend/                     # Python FastAPI Backend
│   ├── app/
│   │   ├── agents/              # AI Agent definitions (memory, router, task)
│   │   ├── api/                 # API Routes and dependencies
│   │   │   ├── dependencies/    # Dependency injection modules
│   │   │   └── routes/          # API Router modules (chat, files, memory, settings, voice, health)
│   │   ├── core/                # Core configuration, constants, logging, and security
│   │   ├── db/                  # Database setup and connection
│   │   ├── memory/              # Memory management
│   │   ├── schemas/             # Pydantic models (chat, common, memory)
│   │   ├── services/            # Business logic and services (file, llm, memory, settings, voice)
│   │   ├── utils/               # Helper functions and responses
│   │   └── main.py              # App initialization & CORS configuration
│   ├── tests/                   # Backend tests
│   ├── requirements.txt         # Backend Python dependencies
│   └── .env.example             # Example environment variables
│
├── src/                         # React Frontend Source
│   ├── assets/                  # Images, fonts, and styling assets
│   ├── components/              # Reusable UI components
│   │   ├── Orb.jsx              # Pulse orb representing FRIDAY's state (idle, listening, processing, speaking)
│   │   ├── ShaderBackground.jsx # WebGL particle/grid ambient background canvas
│   │   ├── ChatWindow.jsx       # Chat layout and dialogue stream
│   │   ├── ChatMessage.jsx      # Individual bubble formatting for user/assistant messages
│   │   ├── ChatInput.jsx        # Keyboard and microphone action bar
│   │   ├── Sidebar.jsx          # Dashboard navigation (Chats, Notes, Tasks, Settings)
│   │   ├── Navbar.jsx & Footer.jsx # Brand navigation and site layouts
│   │   └── CustomCursor.jsx     # High-fidelity glowing pointer overlay
│   │
│   ├── pages/                   # Main Page Views
│   │   ├── Home.jsx             # Hero landing page featuring the active Orb and tech stack
│   │   ├── Chat.jsx             # Conversational workspace dashboard
│   │   ├── Vision.jsx           # Future plans and project goals tracker
│   │   └── About.jsx            # Deep-dive into project inspiration and boundaries
│   │
│   ├── services/                # API communication layers
│   │   ├── chatService.js       # Conversational message history
│   │   ├── memoryService.js     # User background memory integration
│   │   ├── notesService.js      # Notes synchronization
│   │   ├── settingsService.js   # Theme/voice option management
│   │   └── voiceService.js      # Speech-to-Text and TTS interfaces
│   │
│   ├── context/                 # State providers (ThemeContext, etc.)
│   ├── App.jsx                  # React Router routes setup
│   ├── main.jsx                 # Application entrypoint
│   └── index.css                # Global styles, fonts, and Tailwind directives
│
├── index.html                   # Entry HTML page
├── package.json                 # Node package configuration
├── vite.config.js               # Vite compilation plugin mappings
└── README.md                    # This documentation file
```

---

## ✨ Implemented Features

1.  **Dynamic Interactive Core (`Orb.jsx`)**: Renders the central glowing core of F.R.I.D.A.Y. utilizing Framer Motion. The Orb morphs dynamically between states:
    - `idle`: Smooth breathing animation.
    - `listening`: Reactive scale ripples pulsing outwards.
    - `processing`: High-speed orbital rotation.
    - `speaking`: Fluid expanding waves indicating voice output.
2.  **Cyberspace Background (`ShaderBackground.jsx`)**: Utilizes custom WebGL fragment shaders on an HTML5 canvas to render a glowing grid background that reacts to window resizing and user interactions.
3.  **Unified Conversational Voice System**: Full-screen Voice Overlay UI backed by a robust `VoiceStateMachine`. Includes robust cross-browser MIME validation for microphone uploads.
    - **Speech-to-Text (STT)**: Powered by `faster-whisper` (`distil-large-v3`).
    - **Text-to-Speech (TTS)**: Powered by `kokoro-onnx`.
4.  **Multi-LLM Routing**: Supports dynamic provider switching between Groq, Gemini, OpenRouter, and Nvidia via a unified LangChain/litellm backend.
5.  **Modular AI Dashboard & Persistence**: Fully equipped with Chat threads, Settings, Notes, and Tasks. All data is actively persisted to a local **SQLite** database.
6.  **Production-Ready Deployment**: Configured for Render via `render.yaml`. Heavy AI models are downloaded during the build phase and lazily loaded into memory in a thread-safe manner to ensure lightning-fast startup times without timeouts.

---

## ⚡ Getting Started

### 🖥️ Frontend Setup

To run the React dashboard:

```bash
# Navigate to the project root
cd Projects/Friday

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
cd Projects/Friday/backend

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
