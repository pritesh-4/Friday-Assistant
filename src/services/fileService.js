import { mockFiles } from "../data/files";
import { simulateApiDelay } from "./api";

/**
 * Service to simulate workspace file upload scopes.
 */
export const fileService = {
  /**
   * Retrieves mock active files.
   * @returns {Promise<Array>} List of session files.
   */
  async getFiles() {
    await simulateApiDelay(400);
    return [...mockFiles];
  },

  /**
   * Mock uploads session configuration file.
   * @param {Object} file - File payload parameter.
   * @returns {Promise<Object>} Formatted file output details.
   */
  async uploadFile(file) {
    await simulateApiDelay(600);
    const newFile = {
      id: `file-${Date.now()}`,
      name: file.name || "unnamed-document.pdf",
      size: file.size || "450 KB",
      type: file.type || "unknown",
      createdAt: new Date().toISOString()
    };
    return newFile;
  },

  /**
   * Deletes session files.
   * @param {string} id - Target file ID.
   * @returns {Promise<boolean>} Completion indicator.
   */
  async deleteFile(id) {
    await simulateApiDelay(300);
    console.log(`TODO: Connect storage API wrapper to delete file ${id}`);
    return true;
  }
};
