import { API_BASE_URL } from "../api";

/**
 * Voice debug trace logger.
 * Enable by setting `localStorage.setItem('FRIDAY_VOICE_DEBUG', 'true')` in browser console.
 * Disable by removing the key or setting to any other value.
 */
function _vtrace(...args) {
  try {
    if (typeof localStorage !== 'undefined' && localStorage.getItem('FRIDAY_VOICE_DEBUG') === 'true') {
      const now = new Date();
      const ts = `${String(now.getHours()).padStart(2, '0')}:${String(now.getMinutes()).padStart(2, '0')}:${String(now.getSeconds()).padStart(2, '0')}.${String(now.getMilliseconds()).padStart(3, '0')}`;
      console.log(`[VOICE-TRACE] ${ts}`, ...args);
    }
  } catch { /* ignore in non-browser environments */ }
}

/**
 * VoiceStreamService — Real-time persistent PCM audio capture and WebSocket streaming.
 *
 * Keeps a single persistent WebSocket connection and microphone stream active
 * throughout the entire conversational session. Controls audio streaming to the
 * backend using the `isStreaming` flag.
 *
 * Runs local VAD (Voice Activity Detection) continuously:
 *   - When streaming: detects silence to trigger the stop command.
 *   - When not streaming (assistant is speaking/thinking): detects user speech
 *     to trigger the client-side barge-in interruption.
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
    onVADStop,
    onBargeIn,        // Called when user speaks during assistant playback
  } = {}) {
    this.socket = null;
    this.audioContext = null;
    this.microphoneSource = null;
    this.processorNode = null;
    this.mediaStream = null;
    this.isRecording = false; // Tracks if the service is initialized/running
    this.isStreaming = false; // Tracks if we are sending audio chunks to the backend

    // Callbacks
    this.onTranscript   = onTranscript   || (() => {});
    this.onStatus       = onStatus       || (() => {});
    this.onContent      = onContent      || (() => {});
    this.onSentence     = onSentence     || (() => {});
    this.onDone         = onDone         || (() => {});
    this.onError        = onError        || (() => {});
    this.onVolumeChange = onVolumeChange || (() => {});
    this.onVADStop      = onVADStop      || (() => {});
    this.onBargeIn      = onBargeIn      || (() => {});

    // VAD & Adaptive Noise Floor Configuration
    this.MIN_SPEECH_THRESHOLD = 0.025;
    this.MAX_SPEECH_THRESHOLD = 0.150;
    this.SPEECH_RATIO         = 2.2;
    this.NOISE_MARGIN         = 0.015;
    this.SILENCE_TIMEOUT_MS   = 750;
    this.MAX_UTTERANCE_MS     = 15000; // 15s safety cap to prevent hung recording

    this.noiseFloor           = 0.010;
    this.isVoiceActive        = false;
    this.silenceStart         = null;
    this.recordingStartTime   = null;

    // Tracker for barge-in eligibility (is the assistant currently active?)
    this.assistantIsActive    = false;
  }

  setAssistantActive(active) {
    this.assistantIsActive = active;
  }

  async start(conversationId = null) {
    const t0 = performance.now();
    console.log(
      "======== STAGE START ========\nStage Name: VoiceStreamService.start\nTimestamp: " +
        new Date().toISOString()
    );

    // If already initialized and WebSocket is connected, just resume streaming
    if (this.isRecording && this.socket && this.socket.readyState === WebSocket.OPEN) {
      console.log("[VOICE-WS] Reusing existing WebSocket connection. Resuming stream.");
      this.isStreaming = true;
      this.isVoiceActive = false;
      this.silenceStart = null;
      this.recordingStartTime = performance.now();
      return;
    }

    // Clean up any stale state before opening a fresh connection
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
              this.onSentence(message.content || message.text || "");
              break;
            case "done":
              this.onDone(message.metrics || {});
              break;
            case "error":
              this.onError(new Error(message.message));
              break;
            case "interrupted":
              console.log("[VOICE-WS] Generation interrupted successfully on backend.");
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
      this.isRecording        = true;
      this.isStreaming        = true;
      this.isVoiceActive      = false;
      this.silenceStart       = null;
      this.recordingStartTime = performance.now();

      /**
       * Unified audio chunk handler — runs for both AudioWorklet and
       * ScriptProcessorNode paths with adaptive noise floor calibration.
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

        // Dynamic Speech Threshold Calculation based on adaptive noise floor
        const currentSpeechThreshold = Math.min(
          this.MAX_SPEECH_THRESHOLD,
          Math.max(this.MIN_SPEECH_THRESHOLD, this.noiseFloor * this.SPEECH_RATIO + this.NOISE_MARGIN)
        );

        // Normalize volume output for UI, subtracting ambient noise floor
        const normalizedVol = Math.min(1, Math.max(0, (rms - this.noiseFloor) * 12));
        this.onVolumeChange(normalizedVol);

        // Speculative VAD checks
        if (this.isStreaming) {
          // Check safety max utterance timeout to prevent indefinite recording
          const utteranceDuration = performance.now() - (this.recordingStartTime || performance.now());
          if (utteranceDuration > this.MAX_UTTERANCE_MS) {
            _vtrace(`VAD: Max utterance duration reached (${Math.round(utteranceDuration)}ms). Triggering stop.`);
            console.log("[VOICE-WS] Max utterance duration reached, finalizing turn.");
            this.isVoiceActive = false;
            this.silenceStart  = null;
            this.triggerStop();
            return;
          }

          // User is speaking: monitor for silence to trigger stop
          if (rms > currentSpeechThreshold) {
            if (!this.isVoiceActive) {
              _vtrace(`VAD: Voice START detected (RMS: ${rms.toFixed(4)} > Threshold: ${currentSpeechThreshold.toFixed(4)}, NoiseFloor: ${this.noiseFloor.toFixed(4)})`);
            }
            this.isVoiceActive = true;
            this.silenceStart  = null;
          } else {
            // Below speech threshold
            if (this.isVoiceActive) {
              if (this.silenceStart === null) {
                this.silenceStart = performance.now();
                _vtrace(`VAD: Silence started (RMS: ${rms.toFixed(4)} <= Threshold: ${currentSpeechThreshold.toFixed(4)})`);
              } else {
                const silenceDuration = performance.now() - this.silenceStart;
                if (silenceDuration > this.SILENCE_TIMEOUT_MS) {
                  _vtrace(`VAD: Silence threshold crossed (${Math.round(silenceDuration)}ms >= ${this.SILENCE_TIMEOUT_MS}ms)`);
                  console.log("[VOICE-WS] VAD triggered silence stop");
                  this.isVoiceActive = false;
                  this.silenceStart  = null;
                  this.triggerStop();
                  return;
                }
              }
            } else {
              // Not currently speaking: adaptively update ambient noise floor via EMA
              this.noiseFloor = this.noiseFloor * 0.95 + rms * 0.05;
            }
          }

          // Downsample and stream chunks to backend
          const downsampled = this.downsampleBuffer(
            float32Samples,
            inputSampleRate,
            targetSampleRate
          );
          const pcmBuffer = this.convertFloat32ToInt16(downsampled);

          if (this.socket && this.socket.readyState === WebSocket.OPEN) {
            this.socket.send(pcmBuffer);
          }
        } else if (this.assistantIsActive) {
          // Assistant is responding/speaking: check for user barge-in
          if (rms > currentSpeechThreshold) {
            console.log("[VOICE-WS] VAD detected user barge-in speaking.");
            this.onBargeIn();
          } else {
            this.noiseFloor = this.noiseFloor * 0.95 + rms * 0.05;
          }
        }
      };

      if (useWorklet) {
        // ── AudioWorklet path (off-main-thread) ──────────────────────────
        this.processorNode = new AudioWorkletNode(this.audioContext, "pcm-processor");
        this.microphoneSource.connect(this.processorNode);

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
        this.processorNode.connect(this.audioContext.destination);

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
   * Send stop signal to backend and pause local streaming.
   * Keeps WebSocket and microphone active.
   */
  triggerStop() {
    if (!this.isStreaming) return;

    _vtrace('Stop signal → backend (triggerStop called)');
    console.log("[VOICE-WS] Sending stop signal to backend");
    if (this.socket && this.socket.readyState === WebSocket.OPEN) {
      this.socket.send(JSON.stringify({ type: "stop" }));
    }

    // Pause audio streaming to backend, but keep the connection open for responses
    this.isStreaming = false;

    // Notify the session manager so it can start the watchdog timer
    this.onVADStop();
  }

  /**
   * Send interrupt signal to backend to cancel active generation.
   */
  interrupt() {
    console.log("[VOICE-WS] Sending interrupt signal to backend");
    if (this.socket && this.socket.readyState === WebSocket.OPEN) {
      this.socket.send(JSON.stringify({ type: "interrupt" }));
    }
    this.isStreaming = false;
    this.assistantIsActive = false;
  }

  /**
   * External stop — triggered by the UI stop button.
   */
  stop() {
    this.triggerStop();
    this.cleanup();
  }

  /**
   * Release all held resources.
   */
  cleanup() {
    this.isRecording = false;
    this.isStreaming = false;
    this.assistantIsActive = false;

    if (this.processorNode) {
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
