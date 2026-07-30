/**
 * PCM Audio Worklet Processor — F.R.I.D.A.Y. Voice System
 *
 * Runs inside an AudioWorkletGlobalScope (off the main UI thread).
 * Accumulates raw float32 PCM samples from the microphone graph and posts
 * them to the main thread in configurable chunk sizes.
 *
 * This replaces the deprecated ScriptProcessorNode (createScriptProcessor),
 * which ran on the main thread and caused UI jank during voice recording.
 *
 * Usage:
 *   await audioContext.audioWorklet.addModule('/pcm-processor.js');
 *   const node = new AudioWorkletNode(audioContext, 'pcm-processor');
 *   node.port.onmessage = (e) => { if (e.data.type === 'chunk') ... };
 *
 * Messages from main thread:
 *   { type: 'stop' }  — Stops processing and terminates the worklet node.
 */
class PCMProcessor extends AudioWorkletProcessor {
  constructor(options) {
    super();

    // Number of float32 samples per emitted chunk.
    // 4096 samples ≈ 256ms at 16 kHz — same as the old ScriptProcessor buffer size.
    this._chunkSize =
      (options &&
        options.processorOptions &&
        options.processorOptions.chunkSize) ||
      4096;

    this._sampleBuffer = [];
    this._active = true;

    // Listen for control messages from the main thread.
    this.port.onmessage = (event) => {
      if (event.data && event.data.type === "stop") {
        this._active = false;
      }
    };
  }

  /**
   * Called every render quantum (~128 samples) by the audio graph.
   * @param {Float32Array[][]} inputs - Array of input channel arrays.
   * @returns {boolean} true = keep node alive; false = allow garbage collection.
   */
  process(inputs) {
    if (!this._active) return false;

    const input = inputs[0];
    if (!input || !input[0]) return true;

    // Only use channel 0 (mono). Stereo is not needed for STT.
    const channelData = input[0];
    for (let i = 0; i < channelData.length; i++) {
      this._sampleBuffer.push(channelData[i]);
    }

    // Emit full chunks with a zero-copy ArrayBuffer transfer.
    while (this._sampleBuffer.length >= this._chunkSize) {
      const chunk = new Float32Array(this._sampleBuffer.splice(0, this._chunkSize));
      this.port.postMessage({ type: "chunk", samples: chunk }, [chunk.buffer]);
    }

    return true;
  }
}

registerProcessor("pcm-processor", PCMProcessor);
