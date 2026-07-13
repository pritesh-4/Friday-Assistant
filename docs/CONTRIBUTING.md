# CONTRIBUTING

> **Purpose**: Guidelines for setting up, developing, and submitting changes to FRIDAY.
> **Scope**: Developer workflow.
> **Last Updated**: 2026-07-13
> **Related Documents**: [DEVELOPMENT_GUIDE.md](./DEVELOPMENT_GUIDE.md), [TESTING.md](./TESTING.md)

## Quick Summary
Welcome to FRIDAY! This document outlines how to get the project running locally and the standards expected for all contributions.

---

## Setup

### Prerequisites
- Node.js (v18+)
- Python (v3.10+)
- API Keys for LLM Providers (e.g., `OPENAI_API_KEY`)

### Running Frontend
```bash
cd frontend
npm install
npm run dev
```
Runs on `http://localhost:5173`.

### Running Backend
```bash
cd backend
python -m venv venv
source venv/bin/activate  # or `venv\Scripts\activate` on Windows
pip install -r requirements.txt
uvicorn app.main:app --reload
```
Runs on `http://localhost:8000`. API docs at `http://localhost:8000/docs`.

---

## Git Workflow

1. **Fork/Clone** the repository.
2. **Create a branch** from `main`.
3. **Make changes** and test thoroughly.
4. **Submit a Pull Request** against `main`.

### Branch Naming
- `feature/short-description` (e.g., `feature/orb-animations`)
- `fix/short-description` (e.g., `fix/websocket-disconnect`)
- `docs/short-description` (e.g., `docs/update-readme`)

### Commit Conventions
Follow [Conventional Commits](https://www.conventionalcommits.org/):
- `feat: added long term memory`
- `fix: resolved audio latency issue`
- `style: updated button padding`
- `refactor: split agent router`

---

## Coding Style & Folder Conventions

- **Frontend**: Use functional components and Hooks. Strictly use the defined CSS design tokens. No inline styles unless dynamically calculated by framer-motion. Keep files under 200 lines where possible.
- **Backend**: Type hint everything in Python. Use Pydantic models for all data validation. Ensure all I/O is async. 
- Follow existing folder structures. See `FRONTEND_ARCHITECTURE.md` and `BACKEND_ARCHITECTURE.md`.

## Pull Request Process
1. Ensure the code passes all linters (`npm run lint` / `flake8`).
2. Provide a clear summary of changes in the PR description.
3. Include screenshots or videos for UI changes (Mandatory for Orb updates).
4. Request review from a maintainer.
