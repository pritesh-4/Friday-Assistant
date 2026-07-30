import { API_BASE_URL } from "../api";

/**
 * VoiceStreamService — Real-time PCM audio capture and WebSocket streaming.
 *
 * Audio pipeline:
 *   getUserMedia → AudioContext → AudioWorkletNode (pcm-processor.js)
 *               → [downsample to 16kHz] → [Int16 encode] → WebSocket binary
 *
 * Falls back to the deprecated ScriptProcessorNode when AudioWorklet is
 * unavailable (e.g. HTTP context without secure origin, old browsers).
 *
 * VAD (Voice Activity Detection) is performed on each audio chunk by computing
 * the RMS amplitude. When silence exceeds SILENCE_TIMEOUT_MS after speech,
 * `triggerStop()` is called to finalize the turn.
 */
export class VoiceStreamService {
  constructor({
    onTranscript,
    onStatus,
    onContent,
    onSentence,
    onDone,
    onError,
    onVolumeChange,
    onVADStop,        // Called when VAD-triggered silence stop fires
  } = {}) {
    this.socket = null;
    this.audioContext = null;
    this.microphoneSource = null;
    this.processorNode = null;
    this.mediaStream = null;
    this.isRecording = false;

    // Callbacks
    this.onTranscript   = onTranscript   || (() => {});
    this.onStatus       = onStatus       || (() => {});
    this.onContent      = onContent      || (() => {});
    this.onSentence     = onSentence     || (() => {});
    this.onDone         = onDone         || (() => {});
    this.onError        = onError        || (() => {});
    this.onVolumeChange = onVolumeChange || (() => {});
    this.onVADStop      = onVADStop      || (() => {});

    // VAD configuration
    this.VOICE_THRESHOLD    = 0.02;
    this.SILENCE_TIMEOUT_MS = 1500;
    this.isVoiceActive      = false;
    this.silenceStart       = null;
  }

  async start(conversationId = null) {
    const t0 = performance.now();
    console.log(
      "======== STAGE START ========\nStage Name: VoiceStreamService.start\nTimestamp: " +
        new Date().toISOString()
    );

    // Unconditionally clean up any previous resources (socket, tracks, AudioContext)
    // before starting a new recording session or turn. This prevents connection leaks
    // during multi-turn conversations and user interruptions.
    this.cleanup();

    try {
      // ── 1. Microphone access ────────────────────────────────────────────
      this.mediaStream = await navigator.mediaDevices.getUserMedia({
        audio: {
          echoCancellation: true,
          noiseSuppression: true,
          autoGainControl: true,
        },
      });

      // ── 2. AudioContext ─────────────────────────────────────────────────
      const AudioContextClass = window.AudioContext || window.webkitAudioContext;
      this.audioContext       = new AudioContextClass();
      const inputSampleRate   = this.audioContext.sampleRate;
      const targetSampleRate  = 16000;

      this.microphoneSource = this.audioContext.createMediaStreamSource(this.mediaStream);

      // ── 3. AudioWorklet (preferred) or ScriptProcessor (fallback) ───────
      let useWorklet = false;

      if (this.audioContext.audioWorklet) {
        try {
          await this.audioContext.audioWorklet.addModule("/pcm-processor.js");
          useWorklet = true;
        } catch (err) {
          console.warn(
            "[VOICE-WS] AudioWorklet load failed — falling back to ScriptProcessorNode:",
            err
          );
        }
      }

      // ── 4. WebSocket connection ─────────────────────────────────────────
      const wsUrl = API_BASE_URL.replace(/^http/, "ws") + "/api/voice/stream";
      console.log(`[VOICE-WS] Connecting to ${wsUrl}`);
      this.socket            = new WebSocket(wsUrl);
      this.socket.binaryType = "arraybuffer";

      this.socket.onopen = () => {
        console.log("[VOICE-WS] Connected successfully");
        this.socket.send(
          JSON.stringify({ type: "start", conversation_id: conversationId })
        );
      };

      this.socket.onmessage = (event) => {
        try {
          const message = JSON.parse(event.data);

          switch (message.type) {
            case "transcript":
              this.onTranscript(message.text, message.final || false);
              break;
            case "status":
              this.onStatus(message.state);
              break;
            case "chunk":
              this.onContent(message.content);
              break;
            case "sentence":
              // Backend sends { type: "sentence", content: "..." }.
              // Fallback to message.text for legacy compatibility.
              this.onSentence(message.content || message.text || "");
              break;
            case "done":
              this.onDone(message.metrics || {});
              break;
            case "error":
              this.onError(new Error(message.message));
              break;
            default:
              console.log("[VOICE-WS] Unhandled WebSocket message:", message);
          }
        } catch (err) {
          console.error("[VOICE-WS] Failed to parse WebSocket message:", err);
        }
      };

      this.socket.onerror = (err) => {
        console.error("[VOICE-WS] WebSocket error:", err);
        this.onError(new Error("WebSocket streaming error."));
      };

      this.socket.onclose = (event) => {
        console.log(`[VOICE-WS] Connection closed (code: ${event.code})`);
      };

      // ── 5. Start capturing ──────────────────────────────────────────────
      this.isRecording  = true;
      this.isVoiceActive = false;
      this.silenceStart  = null;

      /**
       * Unified audio chunk handler — runs for both AudioWorklet and
       * ScriptProcessorNode paths.
       * @param {Float32Array} float32Samples
       */
      const handleAudioChunk = (float32Samples) => {
        if (!this.isRecording) return;

        // RMS amplitude for VAD and volume visualization
        let sumSquares = 0;
        for (let i = 0; i < float32Samples.length; i++) {
          sumSquares += float32Samples[i] * float32Samples[i];
        }
        const rms = Math.sqrt(sumSquares / float32Samples.length);
        this.onVolumeChange(Math.min(1, rms * 10));

        // VAD State Machine
        if (rms > this.VOICE_THRESHOLD) {
          this.isVoiceActive = true;
          this.silenceStart  = null;
        } else if (this.isVoiceActive) {
          if (this.silenceStart === null) {
            this.silenceStart = performance.now();
          } else {
            const silenceDuration = performance.now() - this.silenceStart;
            if (silenceDuration > this.SILENCE_TIMEOUT_MS) {
              console.log("[VOICE-WS] VAD triggered silence stop");
              this.isVoiceActive = false;
              this.silenceStart  = null;
              this.triggerStop();
              return; // Don't send more audio after triggering stop
            }
          }
        }

        // Downsample from mic sample rate to 16 kHz and encode as Int16
        const downsampled = this.downsampleBuffer(
          float32Samples,
          inputSampleRate,
          targetSampleRate
        );
        const pcmBuffer = this.convertFloat32ToInt16(downsampled);

        if (this.socket && this.socket.readyState === WebSocket.OPEN) {
          this.socket.send(pcmBuffer);
        }
      };

      if (useWorklet) {
        // ── AudioWorklet path (off-main-thread) ──────────────────────────
        this.processorNode = new AudioWorkletNode(this.audioContext, "pcm-processor");
        this.microphoneSource.connect(this.processorNode);
        // No need to connect to destination for capture-only worklets.

        this.processorNode.port.onmessage = (event) => {
          if (event.data && event.data.type === "chunk") {
            handleAudioChunk(event.data.samples);
          }
        };

        console.log("[VOICE-WS] Audio engine: AudioWorkletNode (off-main-thread)");
      } else {
        // ── ScriptProcessorNode fallback (main thread, deprecated) ────────
        this.processorNode = this.audioContext.createScriptProcessor(4096, 1, 1);
        this.microphoneSource.connect(this.processorNode);
        this.processorNode.connect(this.audioContext.destination); // Required to keep node alive

        this.processorNode.onaudioprocess = (e) => {
          handleAudioChunk(e.inputBuffer.getChannelData(0));
        };

        console.warn(
          "[VOICE-WS] Audio engine: ScriptProcessorNode (deprecated fallback — serve over HTTPS/localhost for AudioWorklet support)"
        );
      }

      console.log(
        `======== STAGE END =========\nResult: Success\nElapsed Time: ${performance.now() - t0}ms\nOutput Summary: Streaming recorder started (worklet: ${useWorklet})`
      );
    } catch (err) {
      this.cleanup();
      console.error(
        `======== STAGE END =========\nResult: Error\nElapsed Time: ${performance.now() - t0}ms\nOutput Summary: ${err.message}`
      );
      this.onError(err);
    }
  }

  /**
   * Send stop signal to backend and halt local recording.
   * Called either by VAD silence detection or by the UI stop button.
   */
  triggerStop() {
    if (!this.isRecording) return;

    console.log("[VOICE-WS] Sending stop signal to backend");
    if (this.socket && this.socket.readyState === WebSocket.OPEN) {
      this.socket.send(JSON.stringify({ type: "stop" }));
    }

    // Halt local recording so no more audio chunks are sent.
    this.isRecording = false;

    // Notify the session manager so it can start the watchdog timer
    // and prevent the pipeline from hanging if the backend is slow to respond.
    this.onVADStop();
  }

  /**
   * External stop — triggered by the UI stop button.
   */
  stop() {
    this.triggerStop();
    this.cleanup();
  }

  /**
   * Release all held resources: processor, audio context, mic stream, socket.
   */
  cleanup() {
    this.isRecording = false;

    if (this.processorNode) {
      // Signal the worklet to terminate before disconnecting.
      if (this.processorNode.port) {
        try { this.processorNode.port.postMessage({ type: "stop" }); } catch { /* ignore */ }
        try { this.processorNode.port.close(); } catch { /* ignore */ }
      }
      this.processorNode.disconnect();
      this.processorNode = null;
    }
    if (this.microphoneSource) {
      this.microphoneSource.disconnect();
      this.microphoneSource = null;
    }
    if (this.audioContext && this.audioContext.state !== "closed") {
      this.audioContext.close().catch(() => {});
      this.audioContext = null;
    }
    if (this.mediaStream) {
      this.mediaStream.getTracks().forEach((track) => {
        try { track.stop(); } catch { /* ignore */ }
      });
      this.mediaStream = null;
    }
    if (this.socket) {
      try { this.socket.close(); } catch { /* ignore */ }
      this.socket = null;
    }
    this.onVolumeChange(0);
  }

  // ── Audio utilities ──────────────────────────────────────────────────────

  /**
   * Downsample a Float32 buffer from `inputSampleRate` to `outputSampleRate`
   * using simple averaging (sufficient quality for STT input).
   */
  downsampleBuffer(buffer, inputSampleRate, outputSampleRate) {
    if (inputSampleRate === outputSampleRate) return buffer;

    const sampleRateRatio = inputSampleRate / outputSampleRate;
    const newLength       = Math.round(buffer.length / sampleRateRatio);
    const result          = new Float32Array(newLength);

    let offsetResult = 0;
    let offsetBuffer = 0;
    while (offsetResult < result.length) {
      const nextOffsetBuffer = Math.round((offsetResult + 1) * sampleRateRatio);
      let accum = 0;
      let count = 0;
      for (let i = offsetBuffer; i < nextOffsetBuffer && i < buffer.length; i++) {
        accum += buffer[i];
        count++;
      }
      result[offsetResult] = count > 0 ? accum / count : 0;
      offsetResult++;
      offsetBuffer = nextOffsetBuffer;
    }
    return result;
  }

  /**
   * Convert Float32 [-1, 1] samples to Int16 PCM, returned as an ArrayBuffer.
   */
  convertFloat32ToInt16(buffer) {
    const l   = buffer.length;
    const buf = new Int16Array(l);
    for (let i = 0; i < l; i++) {
      const s = Math.max(-1, Math.min(1, buffer[i]));
      buf[i]  = s < 0 ? s * 0x8000 : s * 0x7fff;
    }
    return buf.buffer;
  }
}
