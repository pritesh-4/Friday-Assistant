import { apiRequest } from "./api";

/**
 * Service for validated private file uploads.
 */
export const fileService = {
  /**
   * Retrieves active files.
   * @returns {Promise<Array>} List of session files.
   */
  async getFiles() {
    return apiRequest("/files");
  },

  /**
   * Uploads session configuration file.
   * @param {Object} file - File payload parameter.
   * @returns {Promise<Object>} Formatted file output details.
   */
  async uploadFile(file) {
    const body = new FormData();
    body.append("file", file);
    return apiRequest("/files", { method: "POST", body });
  },

  /**
   * Deletes session files.
   * @param {string} id - Target file ID.
   * @returns {Promise<boolean>} Completion indicator.
   */
  async deleteFile(id) {
    await apiRequest(`/files/${id}`, { method: "DELETE" });
    return true;
  }
};
