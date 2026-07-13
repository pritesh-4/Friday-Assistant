# DEVELOPMENT_GUIDE

> **Purpose**: Explain the daily development workflow and how to add new features.
> **Scope**: Practical examples of extending the codebase.
> **Last Updated**: 2026-07-13
> **Related Documents**: [CONTRIBUTING.md](./CONTRIBUTING.md), [PROJECT_STRUCTURE.md](./PROJECT_STRUCTURE.md)

## Quick Summary
A quick reference on how and where to add new code when expanding FRIDAY's capabilities.

---

## Adding a Component
**Where**: `src/components/`
**How**:
1. Create a new file (e.g., `WeatherWidget.jsx`).
2. Ensure it is purely presentational or tightly coupled to its specific local state.
3. Use design tokens from `styles/` for all colors and spacing.
4. Export it and import it where needed.

## Adding a Page
**Where**: `src/pages/`
**How**:
1. Create a new page file (e.g., `Settings.jsx`).
2. Wrap it in the main Layout component.
3. Register the new route in the main router configuration (`src/App.jsx` or router file).

## Adding an API Endpoint
**Where**: `app/api/routers/`
**How**:
1. Identify the domain (e.g., `memory`, `chat`, `tools`).
2. Create or update the relevant router file.
3. Define the Pydantic request/response models in `app/schemas/`.
4. Keep the route handler thin; push business logic to `app/services/`.

## Adding a Service
**Where**: `app/services/`
**How**:
1. Create a logical service file (e.g., `spotify_service.py`).
2. Implement async functions that interact with the external API or database.
3. Call these service functions from the API routers or Agent tools.

## Adding a Tool for the Agent
**Where**: `app/agents/tools/`
**How**:
1. Define the tool schema (JSON schema describing parameters).
2. Write the execution logic (often wrapping a function from `app/services/`).
3. Register the tool in the Router Agent's available tools list.
