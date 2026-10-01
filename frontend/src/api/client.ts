export const API_URL = import.meta.env.VITE_API_URL ?? "http://localhost:8000";

// avatar_url from the API is a relative path (e.g. "/users/5/avatar"); this
// resolves it against the backend origin for use in an <img src>.
export function avatarUrl(path: string | null): string | null {
  return path ? `${API_URL}${path}` : null;
}

export class ApiError extends Error {
  status: number;

  constructor(status: number, message: string) {
    super(message);
    this.status = status;
  }
}

async function request<T>(path: string, options: RequestInit = {}): Promise<T> {
  const token = localStorage.getItem("access_token");
  const headers = new Headers(options.headers);
  if (token) {
    headers.set("Authorization", `Bearer ${token}`);
  }

  const response = await fetch(`${API_URL}${path}`, { ...options, headers });

  if (!response.ok) {
    let detail = response.statusText;
    try {
      const body = await response.json();
      detail = body.detail ?? detail;
    } catch {
      // response had no JSON body
    }
    if (response.status === 401) {
      // The JWT is missing/expired/invalid — every call through this helper
      // is already authenticated, so a 401 here always means the session
      // died underneath the user. Send them back to log in again.
      localStorage.removeItem("access_token");
      if (window.location.pathname !== "/login") {
        window.location.href = "/login";
      }
    }
    throw new ApiError(response.status, detail);
  }

  if (response.status === 204) {
    return undefined as T;
  }
  return response.json() as Promise<T>;
}

export function apiGet<T>(path: string): Promise<T> {
  return request<T>(path);
}

export function apiPost<T>(path: string, body: unknown): Promise<T> {
  return request<T>(path, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });
}

export function apiPatch<T>(path: string, body: unknown): Promise<T> {
  return request<T>(path, {
    method: "PATCH",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });
}

export function apiPut<T>(path: string, body: unknown): Promise<T> {
  return request<T>(path, {
    method: "PUT",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });
}

export function apiDelete<T>(path: string): Promise<T> {
  return request<T>(path, { method: "DELETE" });
}

const WAKE_RETRY_DELAY_MS = 2500;
const WAKE_MAX_ATTEMPTS = 36;

// The free-tier backend sleeps when idle and answers with 502/503 or a dropped
// connection while it boots, so a failed load is only conclusive for a 4xx.
export function isServerUnavailable(err: unknown): boolean {
  return !(err instanceof ApiError) || err.status >= 500;
}

export async function loadWhileServerWakes<T>(
  load: () => Promise<T>,
  { onSlow, isCancelled }: { onSlow: () => void; isCancelled: () => boolean },
): Promise<T> {
  for (let attempt = 1; ; attempt++) {
    try {
      return await load();
    } catch (err) {
      if (!isServerUnavailable(err) || attempt >= WAKE_MAX_ATTEMPTS || isCancelled()) throw err;
      onSlow();
      await new Promise((resolve) => setTimeout(resolve, WAKE_RETRY_DELAY_MS));
    }
  }
}
