import { VoiceStateMachine } from "./voiceStateMachine";
import { VoiceStreamService } from "./streamService";
import { speechQueue } from "./speechQueue";

export class VoiceSessionManager {
  constructor({ onStateChange, onStreamEvent, onError, onVolumeChange } = {}) {
    this._stateMachine = new VoiceStateMachine((newState, prevState) => {
      if (onStateChange) onStateChange(newState, prevState);
    });

    this._onStreamEvent = onStreamEvent || (() => {});
    this._onError = onError || (() => {});
    this._onVolumeChange = onVolumeChange || (() => {});

    this._recorder = null;
    this._watchdogTimer = null; 
    this._isDestroyed = false;
    
    this.watchdogTimeoutMs = 120000;
    
    this._activeConversationId = null;
  }

  get state() {
    return this._stateMachine.state;
  }

  get isActive() {
    return this._stateMachine.isActive;
  }

  setConversationId(id) {
    this._activeConversationId = id;
  }

  async open() {
    if (this._isDestroyed) return;
    if (this._stateMachine.isActive) return;

    const ok = this._stateMachine.transition("REQUEST_PERMISSION");
    if (!ok) return;

    await this._startRecording();
  }

  close() {
    this._clearWatchdogTimer();
    speechQueue.stop();

    if (this._recorder) {
      this._recorder.cleanup();
      this._recorder = null;
    }

    this._stateMachine.reset();
  }

  async interrupt() {
    if (this._stateMachine.state === "RESPONDING" || this._stateMachine.state === "THINKING" || this._stateMachine.state === "STREAMING_RESPONSE") {
      speechQueue.stop();
      this._clearWatchdogTimer();
      const ok = this._stateMachine.transition("LISTENING");
      if (ok) {
        await this._startRecording();
      }
    }
  }

  /**
   * Called externally when the user clicks stop or via VAD.
   */
  async stopRecording() {
    if (this._stateMachine.state !== "LISTENING" && this._stateMachine.state !== "RECORDING") return;
    await this._processRecording();
  }

  /**
   * Called externally as sentences arrive from the LLM or immediately for synchronous responses.
   */
  speakResponse(sentence) {
    if (!this._stateMachine.isActive) return;

    if (this._stateMachine.state === "THINKING" || this._stateMachine.state === "STREAMING_RESPONSE" || this._stateMachine.state === "COMPLETE") {
      // Don't forcefully transition to RESPONDING here if we're still STREAMING_RESPONSE,
      // just let the queue consume it. The queue onStart will handle transition.
    }

    const cleanText = sentence
      .replace(/[#*`_>\-[\]()]/g, " ")
      .replace(/\n+/g, " ")
      .trim();

    if (!cleanText) return;
    
    speechQueue.add(
      cleanText,
      () => {
        // onStart
        if (this._stateMachine.isActive && (this._stateMachine.state === "THINKING" || this._stateMachine.state === "STREAMING_RESPONSE" || this._stateMachine.state === "COMPLETE")) {
          this._stateMachine.transition("RESPONDING");
        }
      },
      () => {
        // onEnd
        this._clearWatchdogTimer();
      }
    );
  }

  resumeListeningAfterSpeech() {
    if (this._stateMachine.isActive && (this._stateMachine.state === "RESPONDING" || this._stateMachine.state === "COMPLETE")) {
      this._resumeListening();
    }
  }

  destroy() {
    this._isDestroyed = true;
    this.close();
  }

  async _startRecording() {
    try {
      if (!this._recorder) {
        this._recorder = new VoiceStreamService({
          onTranscript: (text, isFinal) => {
            if (isFinal) {
              const cleanText = text?.trim();
              if (!cleanText) {
                this._clearWatchdogTimer();
                this._resumeListening();
                return;
              }
              this._stateMachine.transition("THINKING");
              this._onStreamEvent("transcript", { text: cleanText });
            }
          },
          onStatus: (state) => {
            this._startWatchdogTimer();
            if (state === "transcribing") {
              this._stateMachine.transition("TRANSCRIBING");
            } else if (state === "processing_intent") {
              this._stateMachine.transition("THINKING");
            }
          },
          onContent: (content) => {
            this._startWatchdogTimer();
            if (this._stateMachine.state === "THINKING") {
              this._stateMachine.transition("STREAMING_RESPONSE");
            }
            this._onStreamEvent("chunk", { content });
          },
          onSentence: (text) => {
            this._onStreamEvent("sentence", { text });
          },
          onDone: (metrics) => {
            if (
              this._stateMachine.state === "STREAMING_RESPONSE" ||
              this._stateMachine.state === "THINKING" ||
              this._stateMachine.state === "TRANSCRIBING"
            ) {
              this._stateMachine.transition("COMPLETE");
            }
            this._onStreamEvent("done", metrics);
            this._clearWatchdogTimer();
          },
          onError: (err) => {
            this._handleError(err.message || "Streaming error occurred.");
          },
          onVolumeChange: (vol) => {
            if (vol > 0.05 && this._stateMachine.state === "LISTENING") {
              this._stateMachine.transition("RECORDING");
            }
            this._onVolumeChange(vol);
          },
          onVADStop: () => {
            // VAD detected silence and sent "stop" to backend.
            // Start the watchdog immediately so a slow/failed backend
            // response doesn't leave the session hung indefinitely.
            this._startWatchdogTimer();
          },
        });
      }

      await this._recorder.start(this._activeConversationId);
      
      if (this._stateMachine.state === "REQUEST_PERMISSION" || this._stateMachine.state === "ERROR") {
        this._stateMachine.transition("READY");
        this._stateMachine.transition("LISTENING");
      }
    } catch (err) {
      this._handleError(err.message || "Failed to access microphone.");
    }
  }

  async _processRecording() {
    console.log(`======== STAGE START ========\nStage Name: Process Recording\nTimestamp: ${new Date().toISOString()}\nInput Summary: Processing recording via WebSocket trigger`);
    const t0 = performance.now();

    const ok = this._stateMachine.transition("UPLOADING");
    if (!ok) {
      console.log(`======== STAGE END =========\nResult: Skipped\nElapsed Time: ${performance.now() - t0}ms\nOutput Summary: Transition UPLOADING not allowed`);
      return;
    }
    
    this._startWatchdogTimer();

    try {
      this._stateMachine.transition("TRANSCRIBING");
      this._recorder.stop();
    } catch (err) {
      this._handleError(err.message || "Recording stop failed.");
    }
  }

  async _resumeListening() {
    if (!this._stateMachine.isActive || this._isDestroyed) return;

    const ok = this._stateMachine.transition("LISTENING");
    if (ok) {
      await this._startRecording();
    }
  }

  _startWatchdogTimer() {
    this._clearWatchdogTimer();
    this._watchdogTimer = setTimeout(() => {
      if (this._stateMachine.isProcessing) {
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
    this._stateMachine.transition("ERROR");
    this._onError(message);
  }

  async retry() {
    if (this._stateMachine.state !== "ERROR") return;
    const ok = this._stateMachine.transition("LISTENING");
    if (ok) {
      await this._startRecording();
    }
  }
}
