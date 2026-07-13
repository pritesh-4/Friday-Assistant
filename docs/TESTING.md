# TESTING

> **Purpose**: Explain testing strategies, tools, and CI/CD integration.
> **Scope**: Testing guidelines.
> **Last Updated**: 2026-07-13
> **Related Documents**: [CONTRIBUTING.md](./CONTRIBUTING.md)

## Quick Summary
Outlines how to ensure code quality through linting, automated testing, and manual verification for the FRIDAY project.

---

## Frontend Testing

### Linting
- **Tool**: ESLint + Prettier
- **Command**: `npm run lint`
- **Rule**: All components must pass lint checks without warnings before a PR is accepted.

### Future Testing Strategy
- **Unit Tests**: Vitest for utility functions and custom hooks.
- **Component Tests**: React Testing Library for verifying Orb states and UI renders.

## Backend Testing

### Linting & Formatting
- **Tools**: Ruff (or Flake8 + Black)
- **Command**: `ruff check .`

### Unit Tests
- **Tool**: Pytest
- **Command**: `pytest`
- **Focus**: Test API routing, data validation schemas (Pydantic), and isolated service logic (mocking external API calls).

### Evals (AI Testing)
Testing non-deterministic LLM output requires a different approach:
- We will implement an `evals` framework to run standard prompts through the Router Agent and assert that the correct tool was selected or the correct intent was classified.

## GitHub Actions / CI
- A backend test workflow (`.github/workflows/backend.yml`) runs automatically.
- It tests API routes, memory services, and ensures correct handling of offline fallbacks via `pytest`.
- (Planned) Automatically run frontend linters and build the Vite frontend on every PR.

## Deployment Checklist
Before pushing to production:
1. Review `.env` configuration.
2. Verify WebSocket connection stability under load.
3. Check UI responsiveness across standard desktop resolutions.
