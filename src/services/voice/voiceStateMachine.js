/**
 * voiceStateMachine.js
 *
 * Deterministic finite state machine for the FRIDAY Voice V2 system.
 * Prevents invalid state transitions and provides event-driven state change notifications.
 *
 * States:
 *   idle       — No voice session active.
 *   permission — Requesting microphone access.
 *   listening  — Mic is active, VAD is monitoring, waiting for user speech.
 *   recording  — VAD detected speech, currently recording audio.
 *   processing — Recording stopped via VAD silence, uploading/transcribing audio.
 *   thinking   — Transcript sent to AI, waiting for streaming response.
 *   speaking   — FRIDAY is speaking the response via concurrent TTS.
 *   error      — A recoverable error occurred.
 */

const VALID_TRANSITIONS = {
  idle:       ["permission", "listening", "error"],
  permission: ["listening", "error", "idle"],
  listening:  ["recording", "processing", "idle", "error"],
  recording:  ["processing", "listening", "idle", "error"],
  processing: ["thinking", "idle", "error"],
  thinking:   ["speaking", "listening", "idle", "error"], // listening if interrupted
  speaking:   ["listening", "idle", "error"],
  error:      ["permission", "listening", "idle"],
};

export class VoiceStateMachine {
  /**
   * @param {function} onChange - Callback invoked with (newState, prevState) on every transition.
   */
  constructor(onChange) {
    this._state = "idle";
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
    this._state = "idle";
    if (prev !== "idle") {
      this._onChange("idle", prev);
      this._listeners.forEach((fn) => fn("idle", prev));
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
    return this._state !== "idle";
  }

  /** @returns {boolean} */
  get isListening() {
    return this._state === "listening";
  }

  /** @returns {boolean} */
  get isRecording() {
    return this._state === "recording";
  }

  /** @returns {boolean} */
  get isSpeaking() {
    return this._state === "speaking";
  }

  /** @returns {boolean} */
  get isProcessing() {
    return this._state === "processing" || this._state === "thinking";
  }
}
