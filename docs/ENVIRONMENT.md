# ENVIRONMENT

> **Purpose**: Document required environment variables and their usage.
> **Scope**: Configuration variables.
> **Last Updated**: 2026-07-13
> **Related Documents**: [SECURITY.md](./SECURITY.md)

## Quick Summary
A comprehensive list of environment variables required to run the frontend and backend of FRIDAY.

> [!CAUTION]
> Never commit actual values or `.env` files to version control. Use `.env.example` as a template.

---

## Backend (`/backend/.env`)

| Variable | Purpose | Required | Example |
|----------|---------|----------|---------|
| `ENVIRONMENT` | Sets the running mode (dev, staging, prod) | Yes | `development` |
| `OPENAI_API_KEY` | Key for OpenAI LLM services | Yes | `sk-...` |
| `ANTHROPIC_API_KEY` | Key for Claude LLM services | No | `sk-ant-...` |
| `DATABASE_URL` | Connection string for the database | Yes | `sqlite:///./friday.db` |
| `ELEVENLABS_API_KEY`| Key for TTS provider | No | `xyz...` |
| `SECRET_KEY` | Used for hashing and JWT signing | Yes | `random_long_string` |

## Frontend (`/frontend/.env`)

*Note: Vite requires frontend variables to be prefixed with `VITE_`.*

| Variable | Purpose | Required | Example |
|----------|---------|----------|---------|
| `VITE_API_URL` | Base URL for REST endpoints | Yes | `http://localhost:8000/api` |
| `VITE_WS_URL` | Base URL for WebSocket connections | Yes | `ws://localhost:8000/ws` |
| `VITE_DEBUG_MODE` | Enables verbose logging in console | No | `true` |

## Local Setup
Copy the example files and fill in your keys:
```bash
cp backend/.env.example backend/.env
cp frontend/.env.example frontend/.env
```
