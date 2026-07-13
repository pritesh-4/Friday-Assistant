# SECURITY

> **Purpose**: Document security practices, API key handling, and vulnerability reporting.
> **Scope**: Project-wide security protocols.
> **Last Updated**: 2026-07-13
> **Related Documents**: [ENVIRONMENT.md](./ENVIRONMENT.md)

## Quick Summary
FRIDAY handles sensitive user data and holds powerful API keys. Security is paramount.

---

## API Key Handling

> [!CAUTION]
> API keys provide access to billable services (OpenAI, Anthropic) and must be rigorously protected.

- **Environment Variables Only**: Keys must only be stored in `.env` files.
- **Backend Only**: Never expose LLM API keys to the frontend. The React app must route all requests through the FastAPI backend.
- **Git Ignore**: Ensure `.env` is in `.gitignore` for both frontend and backend.

## Secret Management
- `SECRET_KEY` in the backend must be a cryptographically secure random string (e.g., generated via `openssl rand -hex 32`).

## Git Rules
- No hardcoded secrets in commits.
- If a secret is accidentally committed, it must be considered compromised. Rotate the key immediately and force-push the history removal, or use a tool like BFG Repo-Cleaner.

## Tool Calling Security (Future)
When FRIDAY is granted access to the local file system or terminal:
- **Sandboxing**: Operations must run in a restricted environment or container.
- **User Approval**: Destructive actions (e.g., deleting files, executing scripts) should require explicit UI confirmation from the user.
- **Scope Limits**: The agent should only have read/write access to a specific `workspace/` directory, not the entire host OS.

## Reporting Vulnerabilities
If you discover a security flaw, do not open a public issue. Contact the repository maintainers privately to allow for a patch before disclosure.
