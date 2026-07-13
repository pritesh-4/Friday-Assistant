const configuredBaseUrl = import.meta.env.VITE_API_URL || "http://127.0.0.1:8000";
export const API_BASE_URL = configuredBaseUrl.replace(/\/$/, "");

export class ApiError extends Error {
  constructor(message, status, details = null) {
    super(message);
    this.name = "ApiError";
    this.status = status;
    this.details = details;
  }
}

/**
 * Make a JSON or multipart request to the FRIDAY FastAPI backend.
 */
export async function apiRequest(path, options = {}) {
  const { body, headers = {}, ...requestOptions } = options;
  const isFormData = body instanceof FormData;
  const requestHeaders = { Accept: "application/json", ...headers };

  if (body && !isFormData) {
    requestHeaders["Content-Type"] = "application/json";
  }

  let response;
  try {
    response = await fetch(`${API_BASE_URL}${path}`, {
      ...requestOptions,
      headers: requestHeaders,
      body: body && !isFormData ? JSON.stringify(body) : body
    });
  } catch {
    throw new ApiError("Unable to reach the FRIDAY backend.", 0);
  }

  if (response.status === 204) return undefined;

  const payload = await response.json().catch(() => null);
  if (!response.ok) {
    throw new ApiError(
      payload?.detail || "The FRIDAY backend could not complete this request.",
      response.status,
      payload?.errors || null
    );
  }
  return payload;
}

/**
 * Retained temporarily for UI-only notification effects that have no backend yet.
 */
export const simulateApiDelay = (ms = 500) =>
  new Promise((resolve) => setTimeout(resolve, ms));
