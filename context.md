# 📑 Project Context & State: F.R.I.D.A.Y.

This file provides a concise, high-level summary of the **F.R.I.D.A.Y.** project's codebase architecture, its current implementation state, and future development steps. It is designed to save context-window tokens for future LLM assistants.

---

## 🧭 Project Overview & Tech Stack

F.R.I.D.A.Y. is a prototype voice-first personal AI operating companion.

*   **Frontend**: React 19 + Vite 8 + React Router DOM v7 (SPA routing)
    *   *Styling & Animations*: Tailwind CSS v4, Framer Motion
    *   *Graphics*: HTML5 Canvas + WebGL custom fragment shaders
*   **Backend**: FastAPI (Python 3.x) + Uvicorn server + Pydantic v2 validation

---

## 📂 Codebase Architecture Map

*   **`/src` (React Frontend)**:
    *   `pages/`: Views for `Home` (landing page with active F.R.I.D.A.Y. Orb), `Chat` (interactive workspace), `Vision` (roadmap details), and `About` (inspiration and boundaries).
    *   `components/`:
        *   [`Orb.jsx`](file:///c:/Users/HP/Documents/c_programm/Projects/Friday/src/components/Orb.jsx): Interactive central component morphing between states (`idle`, `listening`, `processing`, `speaking`).
        *   [`ShaderBackground.jsx`](file:///c:/Users/HP/Documents/c_programm/Projects/Friday/src/components/ShaderBackground.jsx): Canvas shader rendering a digital matrix grid.
        *   `ChatWindow.jsx`, `ChatMessage.jsx`, `ChatInput.jsx`, `Sidebar.jsx`: Chat dashboard frames.
    *   `services/`: Core logic helpers (`chatService.js`, `notesService.js`, `tasksService.js`, `voiceService.js`, `settingsService.js`).
    *   `data/`: Mock data storage matching API schemas.
*   **`/backend` (FastAPI)**:
    *   `app/main.py`: App initiation, CORS config, router mounts.
    *   `app/api/routes/`: API endpoint modules for chat, files, health, memory, settings, and voice.
    *   `app/agents/`: AI agents for memory, routing, and task execution.
    *   `app/services/`: Core logic for LLM interaction, memory, files, and voice processing.
    *   `app/core/`: Configuration, logging, and security setups.
    *   `app/db/`: Database configuration and initialization.
    *   `app/schemas/`: Pydantic models categorized into chat, common, and memory.

---

## ⚡ Current Implementation State

> [!IMPORTANT]
> The application is currently a **fully functional UI mock-up** and **scaffolded backend API**. No real integrations or persistence systems are linked yet.

### 1. Frontend State
*   **State**: Complete UI mockup. Responsive routing, animated components, custom theme context, custom cursor, and dashboard views are fully functional.
*   **Services**: Frontend services (`src/services/*.js`) simulate API delays using `setTimeout` and pull local mock data from `src/data/*.js`.
*   **API Connection**: The frontend does **not** make real HTTP requests to the backend (i.e. no Axios/Fetch calls to the backend uvicorn server).

### 2. Backend State
*   **State**: Scaffolded API structure with agents, services, and db placeholders.
*   **Endpoints**: FastAPI is configured with standard routes matching the application specs (chat, files, health, memory, settings, voice), but they mostly return stub responses or mock data.
*   **Database**: No database (SQLite/PostgreSQL) is currently connected to the backend.

---

## 🚀 Recommended Roadmap for Future LLMs

When continuing development on F.R.I.D.A.Y., focus on the following milestones:

1.  **Frontend-Backend Integration**:
    *   Replace mock service delay calls in `src/services/` with real HTTP calls (e.g. using `fetch` or `axios`) targeting `http://localhost:8000`.
2.  **Backend Persistence**:
    *   Initialize a local SQLite database or database ORM (like SQLAlchemy or Tortoise ORM) inside `backend/`.
    *   Implement database CRUD models inside routers (`chat.py`, `notes.py`, etc.) to replace placeholders.
3.  **LLM / AI Model Integration**:
    *   Implement real LLM providers (e.g., OpenAI SDK, Google Generative AI SDK) in the backend to stream responses to frontend queries.
4.  **Voice Feature Implementation**:
    *   Wire Web Speech APIs (Speech Recognition & Speech Synthesis) inside the frontend (`voiceService.js`) to drive the `listening` and `speaking` states of `Orb.jsx`.
