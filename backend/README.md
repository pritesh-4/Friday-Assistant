# F.R.I.D.A.Y. Backend API

Foundational FastAPI backend setup and boilerplate code powering the FRIDAY personal AI companion.

## Features Included
- **Scalable Folder Structure:** Modular design grouping API routes, schemas, core configurations, and services.
- **Environment Management:** Automated variable loading using `pydantic-settings` from local `.env`.
- **CORS Configured:** Secure and integrated with React frontend clients.
- **Health Checks & Routing:** Pre-routed endpoints for core features (LLM Chat, Memory, Voice, and File Uploads).
- **Service/Agent Layers:** Architecture ready to implement custom business logic and multi-agent interaction systems.
- **Consistent Error Handling:** Built-in JSON response formats for standard errors (e.g. 404, 500).

---

## Local Setup

### 1. Prerequisites
Make sure you have python 3.8+ installed on your system.

### 2. Prepare Virtual Environment
Inside the `backend/` directory, activate your virtual environment:
```bash
# On Windows
.\venv\Scripts\activate

# On Unix or MacOS
source venv/bin/activate
```

### 3. Install Dependencies
```bash
pip install -r requirements.txt
```

### 4. Environment Configuration
Copy the template to initialize your local configuration:
```bash
copy .env.example .env
```
Fill out the required API keys (OpenAI, Gemini, Groq, Nvidia, etc.) in your `.env` file.

### 5. Running the API
Run the server locally with reload enabled:
```bash
uvicorn app.main:app --reload
```

The API will be available at:
- **Server Root:** http://127.0.0.1:8000
- **Interactive Swagger Docs:** http://127.0.0.1:8000/docs
