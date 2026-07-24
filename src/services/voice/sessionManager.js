import { VoiceStateMachine } from "./voiceStateMachine";
import { VoiceRecorderService } from "./recorder";
import { voiceUploadService } from "./uploadService";
import { speechQueue } from "./speechQueue";

export class VoiceSessionManager {
  constructor({ onStateChange, onTranscript, onError, onVolumeChange } = {}) {
    this._stateMachine = new VoiceStateMachine((newState, prevState) => {
      if (onStateChange) onStateChange(newState, prevState);
    });

    this._onTranscript = onTranscript || (() => {});
    this._onError = onError || (() => {});
    this._onVolumeChange = onVolumeChange || (() => {});

    this._recorder = null;
    this._watchdogTimer = null; 
    this._isDestroyed = false;

    this.watchdogTimeoutMs = 30000;
  }

  get state() {
    return this._stateMachine.state;
  }

  get isActive() {
    return this._stateMachine.isActive;
  }

  async open() {
    if (this._isDestroyed) return;
    if (this._stateMachine.isActive) return;

    const ok = this._stateMachine.transition("permission");
    if (!ok) return;

    await this._startRecording();
  }

  close() {
    console.log("[VOICE] Session closed");
    this._clearWatchdogTimer();
    speechQueue.stop();

    if (this._recorder) {
      this._recorder.cleanup();
      this._recorder = null;
    }

    this._stateMachine.reset();
  }

  async interrupt() {
    if (this._stateMachine.state === "speaking" || this._stateMachine.state === "thinking") {
      console.log("[VOICE] User interrupted F.R.I.D.A.Y.");
      speechQueue.stop();
      this._clearWatchdogTimer();
      const ok = this._stateMachine.transition("listening");
      if (ok) {
        await this._startRecording();
      }
    }
  }

  /**
   * Called externally when the user clicks stop or via VAD.
   */
  async stopRecording() {
    if (this._stateMachine.state !== "listening" && this._stateMachine.state !== "recording") return;
    await this._processRecording();
  }

  /**
   * Called externally as sentences arrive from the LLM.
   */
  speakResponse(sentence) {
    if (!this._stateMachine.isActive) return;

    // We can transition to speaking from thinking or while already speaking.
    if (this._stateMachine.state === "thinking") {
      this._stateMachine.transition("speaking");
    }

    const cleanText = sentence
      .replace(/[#*`_>\-[\]()]/g, " ")
      .replace(/\n+/g, " ")
      .trim();

    if (!cleanText) return;

    console.log(`[VOICE] Queueing TTS chunk: "${cleanText}"`);
    
    speechQueue.add(
      cleanText,
      () => {
        // onStart
        if (this._stateMachine.isActive && this._stateMachine.state === "thinking") {
          this._stateMachine.transition("speaking");
        }
      },
      () => {
        // onEnd
        this._clearWatchdogTimer();
        // If queue is empty and we are still speaking (i.e. LLM is fully done and all audio played)
        // Then we resume listening. But wait, how do we know the LLM is done?
        // useVoiceSession.js will call markSpeakingComplete() when LLM is done and queue is empty.
      }
    );
  }

  /**
   * Called by useVoiceSession when the LLM stream finishes AND the speechQueue is empty.
   */
  resumeListeningAfterSpeech() {
    if (this._stateMachine.isActive && this._stateMachine.state === "speaking") {
      console.log("[VOICE] TTS Queue complete and LLM done. Resuming listening.");
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
            if (this._stateMachine.state === "listening") {
              this._stateMachine.transition("recording");
            }
          },
          onVoiceStop: () => {
            if (this._stateMachine.state === "recording") {
              console.log("[VOICE] VAD detected silence, stopping recording.");
              this.stopRecording();
            }
          },
          onVolumeChange: (vol) => this._onVolumeChange(vol)
        });
      }

      await this._recorder.start();
      
      // Successfully got permission and started recording
      if (this._stateMachine.state === "permission" || this._stateMachine.state === "error") {
        this._stateMachine.transition("listening");
      }
    } catch (err) {
      this._handleError(err.message || "Failed to access microphone.");
    }
  }

  async _processRecording() {
    console.log("[VOICE] Upload received");
    console.time("[VOICE_TIME] Upload & STT");
    const ok = this._stateMachine.transition("processing");
    if (!ok) return;
    
    this._startWatchdogTimer();

    let result;
    try {
      result = await this._recorder.stop();
    } catch (err) {
      console.timeEnd("[VOICE_TIME] Upload & STT");
      if (err.message.includes("empty")) {
        console.log("[VOICE] Recording was empty, resuming listening.");
        this._clearWatchdogTimer();
        this._resumeListening();
      } else {
        this._handleError(err.message || "Recording failed.");
      }
      return;
    }

    try {
      console.log("[VOICE] STT started");
      const transcriptionResult = await voiceUploadService.transcribeVoice(
        result.blob,
        result.mimeType || "audio/webm",
        null, 
        3     
      );
      
      console.timeEnd("[VOICE_TIME] Upload & STT");
      console.log("[VOICE] STT finished");

      const transcript = transcriptionResult?.transcript?.trim();
      if (!transcript) {
        console.info("[VOICE] Empty transcription, resuming listening.");
        this._clearWatchdogTimer();
        this._resumeListening();
        return;
      }
      
      console.log(`[VOICE] Transcript: "${transcript}"`);

      const thinkOk = this._stateMachine.transition("thinking");
      if (thinkOk) {
        console.log("[VOICE] Sent transcript to Conversation Manager");
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

  async retry() {
    if (this._stateMachine.state !== "error") return;
    const ok = this._stateMachine.transition("listening");
    if (ok) {
      await this._startRecording();
    }
  }
}
