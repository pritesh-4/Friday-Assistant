/**
 * Production-ready MediaRecorder wrapper service with Voice Activity Detection (VAD).
 * Handles microphone capture, stream lifecycle, audio chunks collection, and resource cleanup.
 * 
 * Uses Web Audio API (AnalyserNode) to detect speech volume and automatically emit
 * onVoiceStart and onVoiceStop events.
 *
 * NOTE: This class is NOT used in the active WebSocket voice streaming path.
 * The WebSocket path uses VoiceStreamService (streamService.js), which has its own
 * built-in VAD running inside the AudioWorklet/ScriptProcessor callback.
 * This class is retained as a legacy fallback for the HTTP upload flow.
 */
export class VoiceRecorderService {
  /**
   * @param {Object} options
   * @param {Function} options.onVoiceStart - Triggered when speech volume exceeds threshold.
   * @param {Function} options.onVoiceStop - Triggered after a period of silence following speech.
   * @param {Function} options.onVolumeChange - (Optional) Triggered with a normalized volume [0, 1] for UI feedback.
   */
  constructor({ onVoiceStart, onVoiceStop, onVolumeChange } = {}) {
    this.mediaRecorder = null;
    this.mediaStream = null;
    this.audioChunks = [];
    this.startTime = 0;

    this.onVoiceStart = onVoiceStart || (() => {});
    this.onVoiceStop = onVoiceStop || (() => {});
    this.onVolumeChange = onVolumeChange || (() => {});

    // VAD (Voice Activity Detection) variables
    this.audioContext = null;
    this.analyser = null;
    this.microphoneSource = null;
    this.vadRafId = null;

    this.isVoiceActive = false;
    this.silenceStart = null;
    
    // VAD Configuration
    // Threshold in root-mean-square amplitude (0 to 1). Needs tuning.
    this.VOICE_THRESHOLD = 0.02; 
    // How long to wait after speech stops before emitting onVoiceStop
    this.SILENCE_TIMEOUT_MS = 1500; 
  }

  static isSupported() {
    return Boolean(
      navigator?.mediaDevices?.getUserMedia &&
        (window.MediaRecorder || window.webkitMediaRecorder)
    );
  }

  static getSupportedMimeType() {
    const types = [
      "audio/webm;codecs=opus",
      "audio/webm",
      "audio/mp4",
      "audio/aac",
      "audio/ogg"
    ];
    for (const type of types) {
      if (MediaRecorder.isTypeSupported(type)) {
        return type;
      }
    }
    return "";
  }

  async start() {
    if (!VoiceRecorderService.isSupported()) {
      throw new Error("Audio recording is not supported in this browser.");
    }

    this.cleanup();

    try {
      this.mediaStream = await navigator.mediaDevices.getUserMedia({
        audio: {
          echoCancellation: true,
          noiseSuppression: true,
          autoGainControl: true
        }
      });
    } catch (err) {
      if (err.name === "NotAllowedError" || err.name === "PermissionDeniedError") {
        throw new Error("Microphone permission denied. Please allow microphone access.", { cause: err });
      } else if (err.name === "NotFoundError" || err.name === "DevicesNotFoundError") {
        throw new Error("No microphone found on this device.", { cause: err });
      } else {
        throw new Error(`Failed to access microphone: ${err.message || "Unknown error"}`, { cause: err });
      }
    }

    const mimeType = VoiceRecorderService.getSupportedMimeType();
    const options = mimeType ? { mimeType } : {};

    try {
      const RecorderClass = window.MediaRecorder || window.webkitMediaRecorder;
      this.mediaRecorder = new RecorderClass(this.mediaStream, options);
    } catch (err) {
      this.cleanup();
      throw new Error(`Failed to initialize MediaRecorder: ${err.message}`, { cause: err });
    }

    this.audioChunks = [];
    this.startTime = Date.now();

    this.mediaRecorder.ondataavailable = (event) => {
      if (event.data && event.data.size > 0) {
        this.audioChunks.push(event.data);
      }
    };

    // Setup Web Audio API for VAD
    this._setupVAD();

    // Start requesting data chunks every 250ms
    this.mediaRecorder.start(250);
  }

  _setupVAD() {
    try {
      const AudioContextClass = window.AudioContext || window.webkitAudioContext;
      this.audioContext = new AudioContextClass();
      
      this.analyser = this.audioContext.createAnalyser();
      this.analyser.fftSize = 512;
      this.analyser.smoothingTimeConstant = 0.4;
      
      this.microphoneSource = this.audioContext.createMediaStreamSource(this.mediaStream);
      this.microphoneSource.connect(this.analyser);
      
      this.isVoiceActive = false;
      this.silenceStart = null;
      
      const bufferLength = this.analyser.frequencyBinCount;
      const dataArray = new Uint8Array(bufferLength);
      
      const detectVoice = () => {
        if (!this.analyser) return;
        
        this.analyser.getByteTimeDomainData(dataArray);
        
        // Calculate RMS (Root Mean Square) for volume detection
        let sumSquares = 0;
        for (let i = 0; i < bufferLength; i++) {
          const normalized = (dataArray[i] / 128.0) - 1.0;
          sumSquares += normalized * normalized;
        }
        const rms = Math.sqrt(sumSquares / bufferLength);
        
        // Expose normalized volume to UI
        this.onVolumeChange(Math.min(1, rms * 10)); // Scale up slightly for UI responsiveness

        if (rms > this.VOICE_THRESHOLD) {
          // Voice detected
          if (!this.isVoiceActive) {
            this.isVoiceActive = true;
            this.onVoiceStart();
          }
          this.silenceStart = null; // reset silence timer
        } else {
          // Silence detected
          if (this.isVoiceActive) {
            if (this.silenceStart === null) {
              this.silenceStart = performance.now();
            } else {
              const silenceDuration = performance.now() - this.silenceStart;
              if (silenceDuration > this.SILENCE_TIMEOUT_MS) {
                this.isVoiceActive = false;
                this.silenceStart = null;
                this.onVoiceStop();
              }
            }
          }
        }
        
        this.vadRafId = requestAnimationFrame(detectVoice);
      };
      
      detectVoice();
    } catch (err) {
      console.warn("Failed to initialize VAD, falling back to manual stop only.", err);
    }
  }

  stop() {
    const stageStartStr = `======== STAGE START ========\nStage Name: MediaRecorder Stop\nTimestamp: ${new Date().toISOString()}\nInput Summary: Stopping recorder`;
    console.log(stageStartStr);
    const t0 = performance.now();

    return new Promise((resolve, reject) => {
      if (!this.mediaRecorder || this.mediaRecorder.state === "inactive") {
        this.cleanup();
        const err = new Error("No active recording to stop.");
        console.error(`======== STAGE END =========\nResult: Error\nElapsed Time: ${performance.now() - t0}ms\nOutput Summary: ${err.message}`);
        reject(err);
        return;
      }

      const mimeType = this.mediaRecorder.mimeType || "audio/webm";

      this.mediaRecorder.onstop = () => {
        const duration = Math.max(0, (Date.now() - this.startTime) / 1000);
        const blob = new Blob(this.audioChunks, { type: mimeType });

        this.cleanup();

        if (blob.size === 0) {
          const err = new Error("Recorded audio is empty.");
          console.error(`======== STAGE END =========\nResult: Error\nElapsed Time: ${performance.now() - t0}ms\nOutput Summary: ${err.message}`);
          reject(err);
          return;
        }

        console.log(`======== STAGE END =========\nResult: Success\nElapsed Time: ${performance.now() - t0}ms\nOutput Summary: Blob size ${blob.size}, type ${mimeType}`);
        resolve({
          blob,
          duration: Math.round(duration),
          mimeType
        });
      };

      this.mediaRecorder.onerror = (event) => {
        this.cleanup();
        const err = new Error(`Recording failed: ${event.error?.name || "Unknown recorder error"}`);
        console.error(`======== STAGE END =========\nResult: Error\nElapsed Time: ${performance.now() - t0}ms\nOutput Summary: ${err.message}`);
        reject(err);
      };

      try {
        this.mediaRecorder.stop();
      } catch (err) {
        this.cleanup();
        const error = new Error(`Failed to stop recorder: ${err.message}`);
        console.error(`======== STAGE END =========\nResult: Error\nElapsed Time: ${performance.now() - t0}ms\nOutput Summary: ${error.message}`);
        reject(error);
      }
    });
  }

  cleanup() {
    if (this.vadRafId !== null) {
      cancelAnimationFrame(this.vadRafId);
      this.vadRafId = null;
    }
    
    if (this.microphoneSource) {
      this.microphoneSource.disconnect();
      this.microphoneSource = null;
    }
    if (this.audioContext && this.audioContext.state !== "closed") {
      this.audioContext.close().catch(() => {});
      this.audioContext = null;
    }
    this.analyser = null;

    if (this.mediaStream) {
      this.mediaStream.getTracks().forEach((track) => {
        try {
          track.stop();
        } catch {
          // ignore track cleanup errors
        }
      });
      this.mediaStream = null;
    }

    if (this.mediaRecorder) {
      this.mediaRecorder.ondataavailable = null;
      this.mediaRecorder.onstop = null;
      this.mediaRecorder.onerror = null;
      this.mediaRecorder = null;
    }

    this.audioChunks = [];
    this.onVolumeChange(0); // reset UI volume
  }
}
