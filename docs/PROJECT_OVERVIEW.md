# PROJECT_OVERVIEW

> **Purpose**: High-level explanation of the FRIDAY project, vision, goals, and philosophy.
> **Scope**: Entire project overview.
> **Last Updated**: 2026-07-13
> **Related Documents**: [ARCHITECTURE.md](./ARCHITECTURE.md), [ROADMAP.md](./ROADMAP.md), [AGENT_CONTEXT.md](./AGENT_CONTEXT.md)

## Quick Summary
FRIDAY is a voice-first, AI-powered intelligent assistant. Inspired by Apple's design, Iron Man's JARVIS/FRIDAY, and Interstellar's TARS, it combines premium visual aesthetics with advanced memory and reasoning capabilities.

## What is FRIDAY?
FRIDAY is an advanced AI assistant designed to run as a cohesive system of frontend interactions, backend processing, and intelligent routing. It features a responsive UI anchored by an animated "Orb" and an agentic backend capable of memory, reasoning, and tool use.

## Vision
To create a seamless, beautiful, and deeply personal AI assistant that feels less like a chat interface and more like an intelligent companion.

## Goals
- **Voice-First Interaction**: Prioritize natural spoken conversation over text input.
- **Premium Aesthetics**: Deliver a stunning visual experience (glassmorphism, fluid animations).
- **Long-term Memory**: Maintain context across sessions and days.
- **Agentic Capabilities**: Execute complex, multi-step tasks using integrated tools.

## Non-Goals
- Replacing standard search engines for simple queries.
- Building a complex text-heavy dashboard.
- Supporting legacy browsers or hardware that cannot run fluid CSS/WebGL animations.

## Development Stage
Currently in early MVP development, focusing on core architecture, frontend foundation, and backend API routing.

## Project Philosophy
1. **Design as a Feature**: Aesthetics matter as much as functionality.
2. **Speed is King**: Minimal latency in voice responses and UI feedback.
3. **Modularity**: Frontend and backend must remain cleanly separated for future scalability (e.g., swapping LLM providers or building a desktop app).

## Core Principles
- **Simplicity**: Code should be readable and components single-purpose.
- **No Duplication**: Maintain a single source of truth for logic and design tokens.
- **Agent-Friendly**: The codebase must be easily navigable by AI coding assistants.
