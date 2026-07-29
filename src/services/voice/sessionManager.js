import { VoiceStateMachine } from "./voiceStateMachine";
import { VoiceRecorderService } from "./recorder";
import { voiceUploadService } from "./uploadService";
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
        this._recorder = new VoiceRecorderService({
          onVoiceStart: () => {
            if (this._stateMachine.state === "LISTENING") {
              this._stateMachine.transition("RECORDING");
            }
          },
          onVoiceStop: () => {
            if (this._stateMachine.state === "RECORDING") {
              this.stopRecording();
            }
          },
          onVolumeChange: (vol) => this._onVolumeChange(vol)
        });
      }

      await this._recorder.start();
      
      if (this._stateMachine.state === "REQUEST_PERMISSION" || this._stateMachine.state === "ERROR") {
        this._stateMachine.transition("READY");
        this._stateMachine.transition("LISTENING");
      }
    } catch (err) {
      this._handleError(err.message || "Failed to access microphone.");
    }
  }

  async _processRecording() {
    console.log(`======== STAGE START ========\nStage Name: Process Recording\nTimestamp: ${new Date().toISOString()}\nInput Summary: Processing recording via state machine`);
    const t0 = performance.now();

    const ok = this._stateMachine.transition("UPLOADING");
    if (!ok) {
      console.log(`======== STAGE END =========\nResult: Skipped\nElapsed Time: ${performance.now() - t0}ms\nOutput Summary: Transition UPLOADING not allowed`);
      return;
    }
    
    this._startWatchdogTimer();

    let result;
    try {
      result = await this._recorder.stop();
    } catch (err) {
      if (err.message.includes("empty")) {
        this._clearWatchdogTimer();
        this._resumeListening();
        console.warn(`======== STAGE END =========\nResult: Empty\nElapsed Time: ${performance.now() - t0}ms\nOutput Summary: Resumed listening after empty recording`);
      } else {
        this._handleError(err.message || "Recording failed.");
        console.error(`======== STAGE END =========\nResult: Error\nElapsed Time: ${performance.now() - t0}ms\nOutput Summary: ${err.message}`);
      }
      return;
    }

    try {
      // Immediately start transcribing transition as upload via fetch begins immediately
      this._stateMachine.transition("TRANSCRIBING");

      await voiceUploadService.orchestrateConversationStream(
        result.blob,
        result.mimeType || "audio/webm",
        this._activeConversationId,
        (eventType, payload) => {
          this._startWatchdogTimer(); // reset on every event

          if (eventType === "transcript") {
            const transcript = payload.text?.trim();
            if (!transcript) {
              this._clearWatchdogTimer();
              this._resumeListening();
              return;
            }
            this._stateMachine.transition("THINKING");
            this._onStreamEvent(eventType, payload);
          } else if (eventType === "metadata") {
            this._onStreamEvent(eventType, payload);
          } else if (eventType === "chunk") {
            if (this._stateMachine.state === "THINKING") {
              this._stateMachine.transition("STREAMING_RESPONSE");
            }
            this._onStreamEvent(eventType, payload);
          } else if (eventType === "sentence") {
            this._onStreamEvent(eventType, payload);
          } else if (eventType === "done") {
            // Complete logic - but TTS queue will likely take over state to RESPONDING
            if (this._stateMachine.state === "STREAMING_RESPONSE" || this._stateMachine.state === "THINKING" || this._stateMachine.state === "TRANSCRIBING") {
              this._stateMachine.transition("COMPLETE");
            }
            this._onStreamEvent(eventType, payload);
            this._clearWatchdogTimer();
          } else if (eventType === "error") {
            this._handleError(payload.content || "Streaming error occurred.");
          }
        }
      );

      // Post-stream safety guard: if the stream ended but state is still stuck
      // in a processing state (e.g. no events were received, or events didn't
      // transition the state), recover by resuming listening.
      if (this._stateMachine.isProcessing) {
        this._clearWatchdogTimer();
        this._resumeListening();
      }
    } catch (err) {
      this._handleError(err.message || "Voice orchestration failed.");
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
