# Project Context & State: F.R.I.D.A.Y.

This file gives a concise, high-level summary of the **F.R.I.D.A.Y.** codebase architecture, the current implementation state, and the next development steps. It is intended to save context for future assistants.

---

## Project Overview & Tech Stack

F.R.I.D.A.Y. is a prototype voice-first personal AI operating companion.

* **Frontend**: React 19 + Vite 8 + React Router DOM v7 for SPA routing.
    * Styling and animations: Tailwind CSS v4, Framer Motion.
    * Graphics: HTML5 Canvas and WebGL custom fragment shaders.
* **Backend**: FastAPI (Python 3.x) + Uvicorn + Pydantic v2 validation.

---

## Codebase Architecture Map

* **`/src`** (React frontend)
    * `pages/`: Views for `Home` (landing page with the active F.R.I.D.A.Y. orb), `Chat` (interactive workspace), `Vision` (roadmap details), and `About` (inspiration and boundaries).
    * `components/`:
        * [`Orb.jsx`](src/components/Orb.jsx): Interactive central component that morphs between the `idle`, `listening`, `processing`, and `speaking` states.
        * [`ShaderBackground.jsx`](src/components/ShaderBackground.jsx): Canvas-based shader background that renders a digital matrix grid.
        * `ChatWindow.jsx`, `ChatMessage.jsx`, `ChatInput.jsx`, `Sidebar.jsx`: Chat dashboard layout components.
    * `services/`: Core logic helpers such as `chatService.js`, `notesService.js`, `tasksService.js`, `voiceService.js`, and `settingsService.js`.
    * `data/`: Mock data storage that matches the expected API schemas.
* **`/backend`** (FastAPI)
    * `app/main.py`: Application startup, CORS configuration, and router mounting.
    * `app/api/routes/`: API endpoint modules for chat, files, health, memory, settings, and voice.
    * `app/agents/`: AI agents for memory, routing, and task execution.
    * `app/services/`: Core logic for LLM interaction, memory, files, and voice processing.
    * `app/core/`: Configuration, logging, and security setup.
    * `app/db/`: Database configuration and initialization.
    * `app/schemas/`: Pydantic models grouped into chat, common, and memory schemas.

---

## Current Implementation State

> [!IMPORTANT]
> The application is currently a **fully functional UI mock-up** with a **scaffolded backend API**. No real integrations or persistence systems are connected yet.

### 1. Frontend State
* **State**: The frontend is a complete UI mock-up. Responsive routing, animated components, custom theme context, custom cursor, and dashboard views are all functional.
* **Services**: Frontend services in `src/services/*.js` simulate API delays with `setTimeout` and read local mock data from `src/data/*.js`.
* **API connection**: The frontend does **not** make real HTTP requests to the backend yet, so there are no Axios or Fetch calls to the Uvicorn server.

### 2. Backend State
* **State**: The backend has a scaffolded API structure with agents, services, and database placeholders.
* **Endpoints**: FastAPI is configured with standard routes that match the app specs (chat, files, health, memory, settings, and voice), but most still return stub responses or mock data.
* **Database**: No database such as SQLite or PostgreSQL is connected yet.

---

## Recommended Roadmap for Future Work

When continuing development on F.R.I.D.A.Y., focus on the following milestones:

1. **Frontend-Backend Integration**:
    * Replace mock service delay calls in `src/services/` with real HTTP calls, for example with `fetch` or `axios`, targeting `http://localhost:8000`.
2. **Backend Persistence**:
    * Initialize a local SQLite database or add an ORM such as SQLAlchemy or Tortoise ORM inside `backend/`.
    * Implement database CRUD models inside routers such as `chat.py` and `notes.py` to replace placeholders.
3. **LLM / AI Model Integration**:
    * Implement real LLM providers such as the OpenAI SDK or Google Generative AI SDK in the backend so responses can stream to the frontend.
4. **Voice Feature Implementation**:
    * Wire Web Speech APIs, including Speech Recognition and Speech Synthesis, into the frontend `voiceService.js` to drive the `listening` and `speaking` states of `Orb.jsx`.

## Extra Notes

* Keep this document short and factual so it stays useful as a handoff note.
* Update the architecture map whenever a new major feature, route, service, or backend module is added.
* If the frontend starts using real API calls, document the base URL and the request flow here.
* If persistence is added, note the database choice and where the initialization logic lives.
