# FRONTEND_ARCHITECTURE

> **Purpose**: Explain the frontend structure, state flow, and routing.
> **Scope**: Client-side application only.
> **Last Updated**: 2026-07-13
> **Related Documents**: [UI_DESIGN_SYSTEM.md](./UI_DESIGN_SYSTEM.md), [COMPONENT_GUIDE.md](./COMPONENT_GUIDE.md)

## Quick Summary
The frontend is a component-driven React application focused on fluid state transitions, minimal latency, and strict adherence to a premium design system.

## Folder Structure

```text
src/
├── assets/       # Static files (images, sounds, icons)
├── components/   # Reusable UI components (e.g., Orb, Buttons, Cards)
├── hooks/        # Custom React hooks (e.g., useAudio, useAgentState)
├── layouts/      # Page wrappers and global layout components
├── pages/        # Top-level route components
├── services/     # API and WebSocket communication logic
├── store/        # Global state management (Zustand/Redux context)
├── styles/       # Global CSS, design tokens, and animations
└── utils/        # Helper functions and formatters
```

## Core Concepts

### Components
All components are highly encapsulated. Presentational components handle visual representation, while container components handle logic.

### State Flow
- **Global State**: Manages the overarching assistant state (`idle`, `listening`, `thinking`, `speaking`, `error`).
- **Local State**: Component-specific toggles (e.g., menu open/closed).
- We prefer lightweight state managers (e.g., Zustand) or React Context over heavy libraries for performance.

### Services & API Communication
All backend interactions are abstracted into the `services/` directory. UI components should never make direct `fetch` calls.
- `api.js`: REST endpoints.
- `websocket.js`: Real-time bidirectional streaming for voice.

### Routing
The app is intentionally mostly single-page, centered around the main interaction screen.
- `/` - Main interface (The Orb).
- `/settings` - Configuration, memory management, provider selection.
