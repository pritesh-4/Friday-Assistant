import { API_BASE_URL } from "../api";

/**
 * Service specifically for handling voice audio uploads.
 * Separated from generic file uploads to ensure precise control over
 * retry logic, progress reporting, and validation handling.
 */

/**
 * Internal shared XHR upload helper with retry and exponential backoff.
 * @param {string} url - The endpoint URL.
 * @param {Blob} blob - The audio blob.
 * @param {string} mimeType - MIME type of the audio.
 * @param {Function} onProgress - Progress callback (0–100).
 * @param {number} retries - Retry attempts remaining.
 * @returns {Promise<Object>} Parsed JSON response.
 */
function _xhrUpload(url, blob, mimeType, onProgress, retries, extraFields = {}) {
  return new Promise((resolve, reject) => {
    const attemptUpload = (attemptsLeft) => {
      const xhr = new XMLHttpRequest();
      xhr.open("POST", url, true);
      xhr.setRequestHeader("Accept", "application/json");
      xhr.timeout = 180000; // 180s timeout (STT + LLM can take time)

      if (onProgress) {
        xhr.upload.onprogress = (event) => {
          if (event.lengthComputable) {
            onProgress(Math.round((event.loaded / event.total) * 100));
          }
        };
      }

      const handleError = (error) => {
        if (attemptsLeft > 0) {
          const backoff = (4 - attemptsLeft) * 1000;
          console.warn(`Upload failed, retrying in ${backoff}ms... (${attemptsLeft} left)`);
          setTimeout(() => attemptUpload(attemptsLeft - 1), backoff);
        } else {
          reject(error);
        }
      };

      xhr.onload = () => {
        if (xhr.status >= 200 && xhr.status < 300) {
          try {
            resolve(JSON.parse(xhr.responseText));
          } catch {
            reject(new Error("Failed to parse server response."));
          }
        } else {
          handleError(new Error(`Server error: ${xhr.status} ${xhr.responseText}`));
        }
      };

      xhr.onerror = () => handleError(new Error("Network error during upload."));
      xhr.ontimeout = () => handleError(new Error("Upload timed out."));

      const ext = mimeType.split("/")[1]?.split(";")[0] || "webm";
      const formData = new FormData();
      formData.append("file", new File([blob], `voice_recording.${ext}`, { type: mimeType }));
      
      for (const [key, value] of Object.entries(extraFields)) {
        formData.append(key, value);
      }
      
      xhr.send(formData);
    };

    attemptUpload(retries);
  });
}

export const voiceUploadService = {
  uploadVoice(blob, mimeType, onProgress, retries = 3) {
    return _xhrUpload(`${API_BASE_URL}/voice/upload`, blob, mimeType, onProgress, retries);
  },

  transcribeVoice(blob, mimeType, onProgress, retries = 3) {
    return _xhrUpload(`${API_BASE_URL}/voice/transcribe`, blob, mimeType, onProgress, retries);
  },
  
  /**
   * Uploads an audio blob to the backend Orchestrator which performs STT and calls the LLM.
   * @param {Blob} blob - The recorded audio blob.
   * @param {string} mimeType - The mime type of the audio.
   * @param {string|null} conversationId - The active conversation ID, if any.
   * @param {Function} onProgress - Callback for upload progress (0–100).
   * @param {number} retries - Number of retry attempts.
   * @returns {Promise<Object>} The orchestration result containing transcript, response, and latencies.
   */
  orchestrateConversation(blob, mimeType, conversationId, onProgress, retries = 3) {
    const extraFields = conversationId ? { conversation_id: conversationId } : {};
    return _xhrUpload(`${API_BASE_URL}/voice/orchestrate`, blob, mimeType, onProgress, retries, extraFields);
  },

  /**
   * Uploads an audio blob and streams the orchestrator response using SSE.
   * @param {Blob} blob - The recorded audio blob.
   * @param {string} mimeType - The mime type of the audio.
   * @param {string|null} conversationId - The active conversation ID.
   * @param {Function} onEvent - Callback for SSE events: (eventType, payload)
   * @returns {Promise<void>} Resolves when the stream is fully consumed.
   */
  async orchestrateConversationStream(blob, mimeType, conversationId, onEvent) {
    console.log(`======== STAGE START ========\nStage Name: Upload & Orchestrate\nTimestamp: ${new Date().toISOString()}\nConversation ID: ${conversationId}\nInput Summary: blob size ${blob.size}`);
    const t0 = performance.now();

    const ext = mimeType.split("/")[1]?.split(";")[0] || "webm";
    const formData = new FormData();
    formData.append("file", new File([blob], `voice_recording.${ext}`, { type: mimeType }));
    
    if (conversationId) {
      formData.append("conversation_id", conversationId);
    }

    let response;
    try {
      console.log(`[UploadService] Fetching ${API_BASE_URL}/voice/orchestrate/stream ...`);
      response = await fetch(`${API_BASE_URL}/voice/orchestrate/stream`, {
        method: "POST",
        headers: {
          "Accept": "text/event-stream"
        },
        body: formData
      });
    } catch (err) {
      console.error(`======== STAGE END =========\nResult: Error\nElapsed Time: ${performance.now() - t0}ms\nOutput Summary: Network fetch failed - ${err.message}`);
      throw err;
    }

    if (!response.ok) {
      const errPayload = await response.json().catch(() => null);
      const errStr = errPayload?.detail || "Streaming request failed";
      console.error(`======== STAGE END =========\nResult: Error\nElapsed Time: ${performance.now() - t0}ms\nOutput Summary: HTTP ${response.status} - ${errStr}`);
      throw new Error(errStr);
    }

    const reader = response.body.getReader();
    const decoder = new TextDecoder();
    let buffer = "";

    try {
      while (true) {
        const { value, done } = await reader.read();
        if (done) break;

        buffer += decoder.decode(value, { stream: true });
        
        const lines = buffer.split("\n\n");
        buffer = lines.pop(); // Keep incomplete chunk in buffer

        for (const line of lines) {
          if (line.startsWith("data: ")) {
            const dataStr = line.slice(6).trim();
            console.log(`[UploadService] Received SSE event: ${dataStr.substring(0, 100)}...`);
            if (dataStr === "[DONE]") {
              onEvent("done", { metrics: {} });
              console.log(`======== STAGE END =========\nResult: Success\nElapsed Time: ${performance.now() - t0}ms\nOutput Summary: Received [DONE]`);
              return;
            }
            try {
              const data = JSON.parse(dataStr);
              onEvent(data.type, data);
              if (data.type === "done" || data.type === "error") {
                console.log(`======== STAGE END =========\nResult: ${data.type === "done" ? "Success" : "Error"}\nElapsed Time: ${performance.now() - t0}ms\nOutput Summary: Received terminal type ${data.type}`);
                return;
              }
            } catch (e) {
              console.warn("Failed to parse SSE JSON:", e);
            }
          }
        }
      }
      console.log(`======== STAGE END =========\nResult: Success\nElapsed Time: ${performance.now() - t0}ms\nOutput Summary: Stream ended normally`);
    } catch (err) {
      console.error(`======== STAGE END =========\nResult: Error\nElapsed Time: ${performance.now() - t0}ms\nOutput Summary: Stream reading error - ${err.message}`);
      throw err;
    } finally {
      reader.releaseLock();
    }
  }
};

