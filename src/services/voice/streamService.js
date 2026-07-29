import { API_BASE_URL } from "../api";

export class VoiceStreamService {
  constructor({
    onTranscript,
    onStatus,
    onContent,
    onSentence,
    onDone,
    onError,
    onVolumeChange
  } = {}) {
    this.socket = null;
    this.audioContext = null;
    this.microphoneSource = null;
    this.processorNode = null;
    this.mediaStream = null;
    this.isRecording = false;

    // Callbacks
    this.onTranscript = onTranscript || (() => {});
    this.onStatus = onStatus || (() => {});
    this.onContent = onContent || (() => {});
    this.onSentence = onSentence || (() => {});
    this.onDone = onDone || (() => {});
    this.onError = onError || (() => {});
    this.onVolumeChange = onVolumeChange || (() => {});

    // VAD Configuration
    this.VOICE_THRESHOLD = 0.02;
    this.SILENCE_TIMEOUT_MS = 1500;
    this.isVoiceActive = false;
    this.silenceStart = null;
  }

  async start(conversationId = null) {
    if (this.isRecording) {
      this.stop();
    }

    const t0 = performance.now();
    console.log("======== STAGE START ========\nStage Name: VoiceStreamService.start\nTimestamp: " + new Date().toISOString());

    try {
      // 1. Get microphone access
      this.mediaStream = await navigator.mediaDevices.getUserMedia({
        audio: {
          echoCancellation: true,
          noiseSuppression: true,
          autoGainControl: true
        }
      });

      // 2. Initialize AudioContext and capture structure
      const AudioContextClass = window.AudioContext || window.webkitAudioContext;
      this.audioContext = new AudioContextClass();
      const inputSampleRate = this.audioContext.sampleRate;
      const targetSampleRate = 16000;

      this.microphoneSource = this.audioContext.createMediaStreamSource(this.mediaStream);

      // Create a ScriptProcessorNode with buffer size 4096, 1 input channel, 1 output channel
      this.processorNode = this.audioContext.createScriptProcessor(4096, 1, 1);
      
      this.microphoneSource.connect(this.processorNode);
      this.processorNode.connect(this.audioContext.destination);

      // 3. Connect to WebSocket
      const wsUrl = API_BASE_URL.replace(/^http/, "ws") + "/api/voice/stream";
      console.log(`[VOICE-WS] Connecting to ${wsUrl}`);
      this.socket = new WebSocket(wsUrl);
      this.socket.binaryType = "arraybuffer";

      this.socket.onopen = () => {
        console.log("[VOICE-WS] Connected successfully");
        this.socket.send(
          JSON.stringify({
            type: "start",
            conversation_id: conversationId
          })
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
            case "content":
              this.onContent(message.content);
              break;
            case "sentence":
              this.onSentence(message.text);
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

      // 4. Start processing and streaming chunks
      this.isRecording = true;
      this.isVoiceActive = false;
      this.silenceStart = null;

      this.processorNode.onaudioprocess = (e) => {
        if (!this.isRecording) return;

        const inputBuffer = e.inputBuffer.getChannelData(0);
        
        // Calculate RMS for VAD
        let sumSquares = 0;
        for (let i = 0; i < inputBuffer.length; i++) {
          sumSquares += inputBuffer[i] * inputBuffer[i];
        }
        const rms = Math.sqrt(sumSquares / inputBuffer.length);

        // Expose volume change
        this.onVolumeChange(Math.min(1, rms * 10));

        // VAD State Machine
        if (rms > this.VOICE_THRESHOLD) {
          this.isVoiceActive = true;
          this.silenceStart = null;
        } else if (this.isVoiceActive) {
          if (this.silenceStart === null) {
            this.silenceStart = performance.now();
          } else {
            const silenceDuration = performance.now() - this.silenceStart;
            if (silenceDuration > this.SILENCE_TIMEOUT_MS) {
              console.log("[VOICE-WS] VAD triggered silence stop");
              this.isVoiceActive = false;
              this.silenceStart = null;
              this.triggerStop();
            }
          }
        }

        // Downsample buffer to 16kHz and convert to Int16
        const downsampled = this.downsampleBuffer(inputBuffer, inputSampleRate, targetSampleRate);
        const pcmBuffer = this.convertFloat32ToInt16(downsampled);

        // Stream binary chunk over WebSocket
        if (this.socket && this.socket.readyState === WebSocket.OPEN) {
          this.socket.send(pcmBuffer);
        }
      };

      console.log(`======== STAGE END =========\nResult: Success\nElapsed Time: ${performance.now() - t0}ms\nOutput Summary: Streaming recorder started`);

    } catch (err) {
      this.cleanup();
      console.error(`======== STAGE END =========\nResult: Error\nElapsed Time: ${performance.now() - t0}ms\nOutput Summary: ${err.message}`);
      this.onError(err);
    }
  }

  triggerStop() {
    if (!this.isRecording) return;
    console.log("[VOICE-WS] Sending stop signal to backend");
    if (this.socket && this.socket.readyState === WebSocket.OPEN) {
      this.socket.send(JSON.stringify({ type: "stop" }));
    }
    // Stop recording locally to prevent streaming silence chunks
    this.isRecording = false;
  }

  stop() {
    this.triggerStop();
    this.cleanup();
  }

  cleanup() {
    this.isRecording = false;
    
    if (this.processorNode) {
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
        try {
          track.stop();
        } catch {
          // Ignore track stop error
        }
      });
      this.mediaStream = null;
    }
    if (this.socket) {
      try {
        this.socket.close();
      } catch {
        // Ignore socket close error
      }
      this.socket = null;
    }
    this.onVolumeChange(0);
  }

  downsampleBuffer(buffer, inputSampleRate, outputSampleRate) {
    if (inputSampleRate === outputSampleRate) {
      return buffer;
    }
    const sampleRateRatio = inputSampleRate / outputSampleRate;
    const newLength = Math.round(buffer.length / sampleRateRatio);
    const result = new Float32Array(newLength);
    
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
      result[offsetResult] = accum / count;
      offsetResult++;
      offsetBuffer = nextOffsetBuffer;
    }
    return result;
  }

  convertFloat32ToInt16(buffer) {
    const l = buffer.length;
    const buf = new Int16Array(l);
    for (let i = 0; i < l; i++) {
      let s = Math.max(-1, Math.min(1, buffer[i]));
      buf[i] = s < 0 ? s * 0x8000 : s * 0x7FFF;
    }
    return buf.buffer;
  }
}
