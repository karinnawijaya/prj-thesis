const DEFAULT_TIMEOUT = 8000;

export interface ApiError extends Error {
  status?: number;
}

export async function apiFetch<T>(
  path: string,
  options: RequestInit = {},
  timeoutMs: number = DEFAULT_TIMEOUT
): Promise<T> {
  const baseUrl = process.env.NEXT_PUBLIC_API_BASE_URL;
  if (!baseUrl) {
    const error: ApiError = new Error("Missing API base URL. Set NEXT_PUBLIC_API_BASE_URL.");
    error.status = 0;
    throw error;
  }

  const controller = new AbortController();
  const timeout = setTimeout(() => controller.abort(), timeoutMs);

  try {
    const response = await fetch(`${baseUrl}${path}`, {
      ...options,
      signal: controller.signal,
      headers: {
        "Content-Type": "application/json",
        ...options.headers,
      },
    });

    if (!response.ok) {
      const message = await response.text();
      const error: ApiError = new Error(
        message || "We ran into an issue while contacting ArtWeave Lite."
      );
      error.status = response.status;
      throw error;
    }

    if (response.status === 204) {
      return {} as T;
    }

    return (await response.json()) as T;
  } catch (error) {
    if ((error as Error).name === "AbortError") {
      const timeoutError: ApiError = new Error(
        "That request took too long. Please try again."
      );
      timeoutError.status = 408;
      throw timeoutError;
    }

    const typedError = error as ApiError;
    if (!typedError.message) {
      typedError.message = "Unexpected error. Please try again.";
    }
    throw typedError;
  } finally {
    clearTimeout(timeout);
  }
}

