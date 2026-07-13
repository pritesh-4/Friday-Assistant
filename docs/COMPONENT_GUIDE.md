# COMPONENT_GUIDE

> **Purpose**: Document every major UI component, its responsibilities, and states.
> **Scope**: Frontend React components.
> **Last Updated**: 2026-07-13
> **Related Documents**: [FRONTEND_ARCHITECTURE.md](./FRONTEND_ARCHITECTURE.md), [UI_DESIGN_SYSTEM.md](./UI_DESIGN_SYSTEM.md)

## Quick Summary
A reference for all reusable and primary components in the FRIDAY UI, detailing their purpose, states, dependencies, and future improvements.

---

## Orb.jsx

**Purpose**: 
Acts as FRIDAY's main visual identity and state indicator.

**Responsibilities**:
- Reacting to audio input/output.
- Displaying current agent state.

**States**:
- *Idle State*: Slow pulsing, waiting for wake word or interaction.
- *Listening State*: Reacts dynamically to user microphone input volume.
- *Thinking State*: Fast, energetic animation indicating backend processing/LLM generation.
- *Speaking State*: Smooth audio waveform or expanding ripples synced to TTS output.
- *Error State*: Red/Amber hue indicating a failure.

**Dependencies**:
- `framer-motion` (for physics-based animations)
- `useAudio` hook (for mic/speaker volume data)

**Props**:
- `state` (enum: idle, listening, thinking, speaking, error)
- `audioData` (array/float for visualizer)

**Future Improvements**:
- WebGL implementation for true 3D fluid simulations instead of CSS/SVG.

---

## ChatTranscript.jsx

**Purpose**: 
Displays the text log of the conversation for accessibility and history.

**Responsibilities**:
- Auto-scrolling to the latest message.
- Formatting markdown and code blocks in responses.

**States**:
- *Empty*: No messages yet.
- *Populated*: List of messages.
- *Typing*: Showing a text-generation indicator while streaming.

**Dependencies**:
- `react-markdown`

**Props**:
- `messages` (Array of message objects)

**Future Improvements**:
- Collapsible UI to focus purely on the Orb.

---

## ToolExecutionCard.jsx

**Purpose**: 
Visually represents when FRIDAY is using an external tool or API.

**Responsibilities**:
- Showing loading spinners during tool execution.
- Displaying the result of a tool call (e.g., weather data, calendar event).

**Props**:
- `toolName` (string)
- `status` (string: pending, success, failed)
- `result` (object)

**Future Improvements**:
- Custom rendering components for specific tools (e.g., interactive map for a location tool).
