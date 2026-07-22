/**
 * Production-ready MediaRecorder wrapper service.
 * Handles microphone capture, stream lifecycle, audio chunks collection, and resource cleanup.
 */
export class VoiceRecorderService {
  constructor() {
    this.mediaRecorder = null;
    this.mediaStream = null;
    this.audioChunks = [];
    this.startTime = 0;
  }

  /**
   * Check browser capability for microphone capture and MediaRecorder API.
   * @returns {boolean}
   */
  static isSupported() {
    return Boolean(
      navigator?.mediaDevices?.getUserMedia &&
        (window.MediaRecorder || window.webkitMediaRecorder)
    );
  }

  /**
   * Determine preferred audio MIME type supported by client browser.
   * @returns {string}
   */
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

  /**
   * Request microphone permission and begin recording stream.
   * @returns {Promise<void>}
   */
  async start() {
    if (!VoiceRecorderService.isSupported()) {
      throw new Error("Audio recording is not supported in this browser.");
    }

    // Clean up any existing active session
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

    // Request data every 250ms for smooth chunk collection
    this.mediaRecorder.start(250);
  }

  /**
   * Stop recording and resolve audio blob payload.
   * @returns {Promise<{ blob: Blob, duration: number, mimeType: string }>}
   */
  stop() {
    return new Promise((resolve, reject) => {
      if (!this.mediaRecorder || this.mediaRecorder.state === "inactive") {
        this.cleanup();
        reject(new Error("No active recording to stop."));
        return;
      }

      const mimeType = this.mediaRecorder.mimeType || "audio/webm";

      this.mediaRecorder.onstop = () => {
        const duration = Math.max(0, (Date.now() - this.startTime) / 1000);
        const blob = new Blob(this.audioChunks, { type: mimeType });

        // Release hardware audio tracks immediately
        this.cleanup();

        if (blob.size === 0) {
          reject(new Error("Recorded audio is empty."));
          return;
        }

        resolve({
          blob,
          duration: Math.round(duration),
          mimeType
        });
      };

      this.mediaRecorder.onerror = (event) => {
        this.cleanup();
        reject(new Error(`Recording failed: ${event.error?.name || "Unknown recorder error"}`));
      };

      try {
        this.mediaRecorder.stop();
      } catch (err) {
        this.cleanup();
        reject(new Error(`Failed to stop recorder: ${err.message}`));
      }
    });
  }

  /**
   * Stop all active media stream hardware tracks and nullify references.
   */
  cleanup() {
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
  }
}
