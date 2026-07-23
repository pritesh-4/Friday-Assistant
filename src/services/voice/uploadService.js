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
function _xhrUpload(url, blob, mimeType, onProgress, retries) {
  return new Promise((resolve, reject) => {
    const attemptUpload = (attemptsLeft) => {
      const xhr = new XMLHttpRequest();
      xhr.open("POST", url, true);
      xhr.setRequestHeader("Accept", "application/json");

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
      xhr.send(formData);
    };

    attemptUpload(retries);
  });
}

export const voiceUploadService = {
  /**
   * Uploads an audio blob to the backend (storage only, no transcription).
   * @param {Blob} blob - The recorded audio blob.
   * @param {string} mimeType - The mime type of the audio.
   * @param {Function} onProgress - Callback for upload progress (0–100).
   * @param {number} retries - Number of retry attempts.
   * @returns {Promise<Object>} The uploaded file metadata.
   */
  uploadVoice(blob, mimeType, onProgress, retries = 3) {
    return _xhrUpload(`${API_BASE_URL}/voice/upload`, blob, mimeType, onProgress, retries);
  },

  /**
   * Uploads an audio blob to the backend for transcription (STT).
   * @param {Blob} blob - The recorded audio blob.
   * @param {string} mimeType - The mime type of the audio.
   * @param {Function} onProgress - Callback for upload progress (0–100).
   * @param {number} retries - Number of retry attempts.
   * @returns {Promise<Object>} The transcription result containing transcript and metadata.
   */
  transcribeVoice(blob, mimeType, onProgress, retries = 3) {
    return _xhrUpload(`${API_BASE_URL}/voice/transcribe`, blob, mimeType, onProgress, retries);
  },
};

