import { VoiceStateMachine } from "./voiceStateMachine";
import { VoiceRecorderService } from "./recorder";
import { voiceUploadService } from "./uploadService";
import { speechQueue } from "./speechQueue";

/**
 * VoiceSessionManager
 *
 * Central orchestrator for the FRIDAY voice conversation loop.
 * Owns the state machine and coordinates the full pipeline:
 *
 *   Mic → Record → Upload/Transcribe → sendMessage() → AI Response → TTS → Speaker → Loop
 *
 * Handles:
 *   - Session lifecycle (open / close)
 *   - Recording with configurable silence timeout
 *   - Transcription via backend STT
 *   - Handing transcript to the chat pipeline (via callback)
 *   - TTS playback via speechQueue
 *   - Interruption (cancel speech mid-sentence, resume listening)
 *   - Error recovery
 *   - Resource cleanup
 */
export class VoiceSessionManager {
  /**
   * @param {object} options
   * @param {function} options.onStateChange  - (newState, prevState) callback
   * @param {function} options.onTranscript   - (transcriptText) callback — sends text into chat pipeline
   * @param {function} options.onError        - (errorMessage) callback
   */
  constructor({ onStateChange, onTranscript, onError } = {}) {
    this._stateMachine = new VoiceStateMachine((newState, prevState) => {
      if (onStateChange) onStateChange(newState, prevState);
    });

    this._onTranscript = onTranscript || (() => {});
    this._onError = onError || (() => {});

    this._recorder = null;
    this._silenceTimer = null;
    this._watchdogTimer = null; // Prevent infinite hanging
    this._isDestroyed = false;

    // Configurable silence timeout (ms) before auto-stopping recording.
    this.silenceTimeoutMs = 2500;
    // Watchdog timeout (ms) before forcefully aborting the pipeline.
    this.watchdogTimeoutMs = 30000;
  }

  // ── Public API ──────────────────────────────────────────────────────────────

  /** @returns {string} Current voice state. */
  get state() {
    return this._stateMachine.state;
  }

  /** @returns {boolean} Whether a voice session is active. */
  get isActive() {
    return this._stateMachine.isActive;
  }

  /**
   * Open a voice session and start listening.
   */
  async open() {
    if (this._isDestroyed) return;
    if (this._stateMachine.isActive) return; // Already active

    const ok = this._stateMachine.transition("listening");
    if (!ok) return;

    await this._startRecording();
  }

  close() {
    console.log("[VOICE] Session closed");
    this._clearSilenceTimer();
    this._clearWatchdogTimer();
    speechQueue.stop();

    if (this._recorder) {
      this._recorder.cleanup();
      this._recorder = null;
    }

    this._stateMachine.reset();
  }

  /**
   * Interrupt FRIDAY while speaking — cancel TTS and resume listening.
   */
  async interrupt() {
    if (this._stateMachine.state !== "speaking") return;

    speechQueue.stop();
    const ok = this._stateMachine.transition("listening");
    if (ok) {
      await this._startRecording();
    }
  }

  /**
   * Manually stop recording (e.g., user clicks stop).
   */
  async stopRecording() {
    if (this._stateMachine.state !== "listening") return;
    this._clearSilenceTimer();
    await this._processRecording();
  }

  /**
   * Called externally when the AI response is complete and ready for TTS.
   * @param {string} responseText - The AI's response text.
   */
  speakResponse(responseText) {
    if (!this._stateMachine.isActive) return;

    // Only transition to speaking if we're in thinking state
    if (this._stateMachine.state !== "thinking") return;

    const ok = this._stateMachine.transition("speaking");
    if (!ok) return;

    // Clean markdown artifacts from text before speaking
    const cleanText = responseText
      .replace(/[#*`_>\-[\]()]/g, " ")
      .replace(/\n+/g, " ")
      .trim();

    if (!cleanText) {
      // Empty response — skip TTS and resume listening
      console.log("[VOICE] Empty AI text response, skipping TTS.");
      this._clearWatchdogTimer();
      this._resumeListening();
      return;
    }

    console.log("[VOICE] TTS generation started");
    console.time("[VOICE_TIME] TTS Generation & Playback");
    speechQueue.add(
      cleanText,
      () => {
        console.timeLog("[VOICE_TIME] TTS Generation & Playback", "- playback started");
      }, // onStart
      () => {
        console.timeEnd("[VOICE_TIME] TTS Generation & Playback");
        console.log("[VOICE] TTS playback finished");
        this._clearWatchdogTimer();
        // TTS finished — resume listening if session is still active
        if (this._stateMachine.isActive && this._stateMachine.state === "speaking") {
          this._resumeListening();
        }
      }
    );
  }

  /**
   * Destroy this manager instance. Called on component unmount.
   */
  destroy() {
    this._isDestroyed = true;
    this.close();
  }

  // ── Internal Methods ────────────────────────────────────────────────────────

  async _startRecording() {
    try {
      if (!this._recorder) {
        this._recorder = new VoiceRecorderService();
      }

      await this._recorder.start();
      this._startSilenceTimer();
    } catch (err) {
      this._handleError(err.message || "Failed to access microphone.");
    }
  }

  async _processRecording() {
    console.log("[VOICE] Upload received");
    console.time("[VOICE_TIME] Upload & STT");
    const ok = this._stateMachine.transition("processing");
    if (!ok) return;
    
    this._startWatchdogTimer(); // Start 30s watchdog when processing begins

    let result;
    try {
      result = await this._recorder.stop();
    } catch (err) {
      console.timeEnd("[VOICE_TIME] Upload & STT");
      this._handleError(err.message || "Recording failed.");
      return;
    }

    // Transcribe via backend
    try {
      console.log("[VOICE] STT started");
      const transcriptionResult = await voiceUploadService.transcribeVoice(
        result.blob,
        result.mimeType || "audio/webm",
        null, // No progress callback for now
        3     // retries
      );
      
      console.timeEnd("[VOICE_TIME] Upload & STT");
      console.log("[VOICE] STT finished");

      const transcript = transcriptionResult?.transcript?.trim();
      if (!transcript) {
        // Silence / no speech detected — resume listening
        console.info("[VOICE] Empty transcription, resuming listening.");
        this._clearWatchdogTimer();
        this._resumeListening();
        return;
      }
      
      console.log(`[VOICE] Transcript: "${transcript}"`);

      // Transition to thinking — the AI pipeline will process this
      const thinkOk = this._stateMachine.transition("thinking");
      if (thinkOk) {
        console.log("[VOICE] Sent transcript to Conversation Manager");
        console.time("[VOICE_TIME] LLM Provider Turnaround");
        this._onTranscript(transcript);
      }
    } catch (err) {
      console.timeEnd("[VOICE_TIME] Upload & STT");
      this._handleError(err.message || "Transcription failed.");
    }
  }

  async _resumeListening() {
    if (!this._stateMachine.isActive || this._isDestroyed) return;

    const ok = this._stateMachine.transition("listening");
    if (ok) {
      await this._startRecording();
    }
  }

  _startSilenceTimer() {
    this._clearSilenceTimer();
    this._silenceTimer = setTimeout(() => {
      if (this._stateMachine.state === "listening") {
        console.log("[VOICE] Silence detected, processing recording.");
        this._processRecording();
      }
    }, this.silenceTimeoutMs);
  }

  _clearSilenceTimer() {
    if (this._silenceTimer) {
      clearTimeout(this._silenceTimer);
      this._silenceTimer = null;
    }
  }
  
  _startWatchdogTimer() {
    this._clearWatchdogTimer();
    this._watchdogTimer = setTimeout(() => {
      if (this._stateMachine.state === "processing" || this._stateMachine.state === "thinking") {
        this._handleError("Pipeline timed out. F.R.I.D.A.Y. took too long to respond.");
      }
    }, this.watchdogTimeoutMs);
  }
  
  _clearWatchdogTimer() {
    if (this._watchdogTimer) {
      clearTimeout(this._watchdogTimer);
      this._watchdogTimer = null;
    }
  }

  _handleError(message) {
    console.error("[VOICE] Error:", message);
    this._clearWatchdogTimer();
    this._stateMachine.transition("error");
    this._onError(message);
  }

  /**
   * Retry from error state — resume listening.
   */
  async retry() {
    if (this._stateMachine.state !== "error") return;
    const ok = this._stateMachine.transition("listening");
    if (ok) {
      await this._startRecording();
    }
  }
}
