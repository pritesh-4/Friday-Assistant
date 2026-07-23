import { API_BASE_URL } from "../api";

/**
 * Service specifically for handling voice audio uploads.
 * Separated from generic file uploads to ensure precise control over
 * retry logic, progress reporting, and validation handling.
 */
export const voiceUploadService = {
  /**
   * Uploads an audio blob to the backend with progress tracking and retries.
   *
   * @param {Blob} blob - The recorded audio blob.
   * @param {string} mimeType - The mime type of the audio.
   * @param {Function} onProgress - Callback for upload progress (0 to 100).
   * @param {number} retries - Number of retry attempts.
   * @returns {Promise<Object>} The uploaded file metadata.
   */
  uploadVoice(blob, mimeType, onProgress, retries = 3) {
    return new Promise((resolve, reject) => {
      const attemptUpload = (attemptsLeft) => {
        const xhr = new XMLHttpRequest();
        const url = `${API_BASE_URL}/voice/upload`;

        xhr.open("POST", url, true);
        xhr.setRequestHeader("Accept", "application/json");

        if (onProgress) {
          xhr.upload.onprogress = (event) => {
            if (event.lengthComputable) {
              const percentComplete = Math.round((event.loaded / event.total) * 100);
              onProgress(percentComplete);
            }
          };
        }

        xhr.onload = () => {
          if (xhr.status >= 200 && xhr.status < 300) {
            try {
              const response = JSON.parse(xhr.responseText);
              resolve(response);
            } catch {
              reject(new Error("Failed to parse response"));
            }
          } else {
            handleError(new Error(`Server error: ${xhr.status} ${xhr.responseText}`));
          }
        };

        xhr.onerror = () => {
          handleError(new Error("Network Error"));
        };

        xhr.ontimeout = () => {
          handleError(new Error("Upload timed out"));
        };

        const handleError = (error) => {
          if (attemptsLeft > 0) {
            console.warn(`Upload failed, retrying... (${attemptsLeft} attempts left)`);
            // Exponential backoff
            const backoff = (4 - attemptsLeft) * 1000;
            setTimeout(() => attemptUpload(attemptsLeft - 1), backoff);
          } else {
            reject(error);
          }
        };

        const formData = new FormData();
        const ext = mimeType.split("/")[1]?.split(";")[0] || "webm";
        const file = new File([blob], `voice_recording.${ext}`, { type: mimeType });
        formData.append("file", file);

        xhr.send(formData);
      };

      attemptUpload(retries);
    });
  },

  /**
   * Uploads an audio blob to the backend for transcription.
   *
   * @param {Blob} blob - The recorded audio blob.
   * @param {string} mimeType - The mime type of the audio.
   * @param {Function} onProgress - Callback for upload progress (0 to 100).
   * @param {number} retries - Number of retry attempts.
   * @returns {Promise<Object>} The transcription result containing the transcript string.
   */
  transcribeVoice(blob, mimeType, onProgress, retries = 3) {
    return new Promise((resolve, reject) => {
      const attemptUpload = (attemptsLeft) => {
        const xhr = new XMLHttpRequest();
        const url = `${API_BASE_URL}/voice/transcribe`;

        xhr.open("POST", url, true);
        xhr.setRequestHeader("Accept", "application/json");

        if (onProgress) {
          xhr.upload.onprogress = (event) => {
            if (event.lengthComputable) {
              const percentComplete = Math.round((event.loaded / event.total) * 100);
              onProgress(percentComplete);
            }
          };
        }

        xhr.onload = () => {
          if (xhr.status >= 200 && xhr.status < 300) {
            try {
              const response = JSON.parse(xhr.responseText);
              resolve(response);
            } catch {
              reject(new Error("Failed to parse response"));
            }
          } else {
            handleError(new Error(`Server error: ${xhr.status} ${xhr.responseText}`));
          }
        };

        xhr.onerror = () => {
          handleError(new Error("Network Error"));
        };

        xhr.ontimeout = () => {
          handleError(new Error("Upload timed out"));
        };

        const handleError = (error) => {
          if (attemptsLeft > 0) {
            console.warn(`Transcription upload failed, retrying... (${attemptsLeft} attempts left)`);
            // Exponential backoff
            const backoff = (4 - attemptsLeft) * 1000;
            setTimeout(() => attemptUpload(attemptsLeft - 1), backoff);
          } else {
            reject(error);
          }
        };

        const formData = new FormData();
        const ext = mimeType.split("/")[1]?.split(";")[0] || "webm";
        const file = new File([blob], `voice_recording.${ext}`, { type: mimeType });
        formData.append("file", file);

        xhr.send(formData);
      };

      attemptUpload(retries);
    });
  }
};
