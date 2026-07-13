# GLOSSARY

> **Purpose**: Explain project-specific terminology.
> **Scope**: Entire project terminology.
> **Last Updated**: 2026-07-13

## Quick Summary
Definitions for the unique terms and concepts used across the FRIDAY project.

---

- **Agent**: The backend AI system responsible for reasoning, memory retrieval, and tool execution.
- **Context**: The set of facts, past messages, and system prompts sent to the LLM to ground its response.
- **Conversation**: A continuous back-and-forth exchange. Grouped logically, sometimes synonymous with Session.
- **Inference**: The process of the LLM generating a response.
- **LLM**: Large Language Model (e.g., GPT-4, Claude 3).
- **Memory**: The system for retaining information. Split into short-term (Session) and long-term (Vector/Profile).
- **Orb**: The primary visual component of the frontend. A reactive, animated sphere that represents FRIDAY's state.
- **Provider**: The external service hosting the LLM (e.g., OpenAI, Anthropic, or a local Ollama instance).
- **Router (Router Agent)**: The initial AI logic gate that determines the user's intent and directs the request to the appropriate sub-system or model.
- **Session**: A specific period of interaction, defined by a unique `session_id`. Often resets after a period of inactivity.
- **Tool Calling**: The ability of the LLM to request the execution of a specific function (e.g., `get_weather(location="NY")`).
- **Workspace**: The user's local directory or environment that FRIDAY may interact with (if computer control is enabled).
