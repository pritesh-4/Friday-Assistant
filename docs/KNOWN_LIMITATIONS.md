# KNOWN_LIMITATIONS

> **Purpose**: Document current limitations, tech debt, and postponed features.
> **Scope**: Project-wide technical constraints.
> **Last Updated**: 2026-07-13
> **Related Documents**: [ROADMAP.md](./ROADMAP.md)

## Quick Summary
A transparent list of what FRIDAY currently *cannot* do, why, and when (or if) it will be fixed.

---

## Current Limitations

- **Audio Latency**: Real-time voice interaction still suffers from 1-2 second latency due to the round-trip of STT -> LLM Inference -> TTS.
  - *Why*: Cloud provider overhead. 
  - *Future Fix*: Moving STT and TTS to local on-device models, and using streaming chunked LLM generation.
- **Context Window Exhaustion**: Very long conversations will eventually hit the LLM context limit.
  - *Why*: Missing advanced summarization pipeline.
  - *Future Fix*: Implement a rolling summarization agent in the background.

## Technical Debt

- **Monolithic Frontend State**: `App.jsx` handles too much global state regarding the socket connection.
  - *Plan*: Refactor into a dedicated `AudioSocketContext` or Zustand store.
- **Hardcoded Prompts**: System prompts are currently hardcoded in Python files.
  - *Plan*: Move to a dedicated Prompt Management system (YAML/JSON) for easier iteration without code changes.

## Features Intentionally Postponed

- **Computer Control (Desktop App)**
  - *Why*: Too risky and complex for MVP. Requires a robust sandboxing strategy.
- **Multi-User Support**
  - *Why*: FRIDAY is currently designed as a personal assistant (1:1). Adding auth and multi-tenant DB schemas slows down MVP development.

## What is Missing
- Comprehensive unit testing for AI generation outputs (evals).
- iOS/Android native companion applications.
