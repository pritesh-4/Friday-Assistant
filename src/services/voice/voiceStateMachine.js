/**
 * voiceStateMachine.js
 *
 * Deterministic finite state machine for the FRIDAY Voice Orchestrator.
 * Prevents invalid state transitions and provides event-driven state change notifications.
 *
 * States:
 *   IDLE               — No voice session active.
 *   REQUEST_PERMISSION — Requesting microphone access.
 *   READY              — Microphone acquired, ready to listen.
 *   LISTENING          — Mic is active, VAD is monitoring, waiting for user speech.
 *   RECORDING          — VAD detected speech, currently recording audio.
 *   UPLOADING          — Sending audio to the Voice Orchestrator API.
 *   TRANSCRIBING       — Waiting for STT completion on the backend.
 *   THINKING           — Waiting for Chat Provider response on the backend.
 *   STREAMING_RESPONSE — Streaming the generated response tokens to the UI.
 *   RESPONDING         — FRIDAY is speaking the response via TTS.
 *   COMPLETE           — Conversation turn finished.
 *   ERROR              — A recoverable error occurred.
 */

const VALID_TRANSITIONS = {
  IDLE:               ["REQUEST_PERMISSION", "LISTENING", "ERROR"],
  REQUEST_PERMISSION: ["READY", "ERROR", "IDLE"],
  READY:              ["LISTENING", "ERROR", "IDLE"],
  LISTENING:          ["RECORDING", "UPLOADING", "IDLE", "ERROR"],
  RECORDING:          ["UPLOADING", "LISTENING", "IDLE", "ERROR"],
  UPLOADING:          ["TRANSCRIBING", "THINKING", "IDLE", "ERROR"],
  TRANSCRIBING:       ["THINKING", "COMPLETE", "LISTENING", "IDLE", "ERROR"],
  THINKING:           ["STREAMING_RESPONSE", "RESPONDING", "LISTENING", "IDLE", "ERROR"], 
  STREAMING_RESPONSE: ["COMPLETE", "RESPONDING", "LISTENING", "IDLE", "ERROR"],
  RESPONDING:         ["COMPLETE", "LISTENING", "IDLE", "ERROR"],
  COMPLETE:           ["LISTENING", "IDLE", "ERROR"],
  ERROR:              ["REQUEST_PERMISSION", "LISTENING", "IDLE"],
};

export class VoiceStateMachine {
  /**
   * @param {function} onChange - Callback invoked with (newState, prevState) on every transition.
   */
  constructor(onChange) {
    this._state = "IDLE";
    this._onChange = onChange || (() => {});
    this._listeners = new Set();
  }

  /** @returns {string} Current state. */
  get state() {
    return this._state;
  }

  /**
   * Attempt a state transition.
   * @param {string} nextState - Target state.
   * @returns {boolean} True if transition succeeded.
   */
  transition(nextState) {
    if (this._state === nextState) return true; // No-op if same state

    const allowed = VALID_TRANSITIONS[this._state];
    if (!allowed || !allowed.includes(nextState)) {
      console.warn(
        `[VoiceStateMachine] Invalid transition: ${this._state} → ${nextState}. ` +
        `Allowed: [${allowed?.join(", ") || "none"}]`
      );
      return false;
    }

    const prev = this._state;
    this._state = nextState;
    this._onChange(nextState, prev);
    this._listeners.forEach((fn) => fn(nextState, prev));
    return true;
  }

  /**
   * Force reset to idle (e.g., on unmount or fatal error).
   */
  reset() {
    const prev = this._state;
    this._state = "IDLE";
    if (prev !== "IDLE") {
      this._onChange("IDLE", prev);
      this._listeners.forEach((fn) => fn("IDLE", prev));
    }
  }

  /**
   * Subscribe to state changes.
   * @param {function} listener - Callback (newState, prevState).
   * @returns {function} Unsubscribe function.
   */
  subscribe(listener) {
    this._listeners.add(listener);
    return () => this._listeners.delete(listener);
  }

  /** @returns {boolean} */
  get isActive() {
    return this._state !== "IDLE";
  }

  /** @returns {boolean} */
  get isListening() {
    return this._state === "LISTENING";
  }

  /** @returns {boolean} */
  get isRecording() {
    return this._state === "RECORDING";
  }

  /** @returns {boolean} */
  get isSpeaking() {
    return this._state === "RESPONDING";
  }

  /** @returns {boolean} */
  get isProcessing() {
    return this._state === "UPLOADING" || this._state === "TRANSCRIBING" || this._state === "THINKING" || this._state === "STREAMING_RESPONSE";
  }
}
