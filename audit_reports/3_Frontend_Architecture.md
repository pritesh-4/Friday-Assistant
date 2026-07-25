# 3. Frontend Architecture

## System Design
The frontend is built using React (Vite) with a heavy emphasis on contextual state management, real-time feedback (SSE), and a fluid, accessible UI.

## Component Breakdown

1. **Pages (src/pages/)**:
   - \Chat.jsx\: The primary interface holding the \ChatWindow\ and \VoiceOverlay\.
   - \Planning.jsx\ & \BackgroundOps.jsx\: Lazy-loaded auxiliary views.
   - \Vision.jsx\ & \About.jsx\: Static/Marketing pages.

2. **Components (src/components/)**:
   - \ChatInput.jsx\: Complex textarea handling global hotkeys (Cmd+K) and auto-resizing.
   - \VoiceOverlay.jsx\: Full-screen takeover during active VAD sessions.
   - \Sidebar.jsx\: Navigational drawer mapping to different memory matrices.

3. **State & Services (src/services/, \src/hooks/\)**:
   - \pi.js\: Centralized axios instance with response interceptors for standardized error extraction (\payload.error.message\).
   - \oiceStateMachine.js\: XState-like object managing transitions (\IDLE\ -> \LISTENING\ -> \UPLOADING\ -> \PROCESSING\ -> \SPEAKING\).
   - \useChat.js\ & \useVoiceSession.js\: Custom hooks abstracting the SSE and WebSocket logic away from the UI components.

## Technical Debt & Findings
- **Mock Data Layer**: The \src/data/\ folder contains dozens of hardcoded mocked responses initially used for rapid prototyping. These are actively leaking into \
otificationService.js\ and \ileService.js\. These MUST be deleted.
- **Console Logs**: Debug statements are scattered across \sessionManager.js\.
- **Bundle Bloat**: While \React.lazy()\ was implemented for auxiliary routes, we must ensure all dead imports (especially to mocked data) are removed so they are pruned from the production bundle.
