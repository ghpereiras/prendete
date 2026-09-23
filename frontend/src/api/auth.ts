import { ApiError, apiGet, apiPost } from "./client";

export interface User {
  id: number;
  email: string;
  full_name: string;
  created_at: string;
}

interface TokenResponse {
  access_token: string;
  token_type: string;
}

export async function login(email: string, password: string): Promise<string> {
  const body = new URLSearchParams({ username: email, password });
  const response = await fetch(
    `${import.meta.env.VITE_API_URL ?? "http://localhost:8000"}/auth/login`,
    { method: "POST", headers: { "Content-Type": "application/x-www-form-urlencoded" }, body },
  );
  if (!response.ok) {
    const data = await response.json().catch(() => ({}));
    throw new ApiError(response.status, data.detail ?? "No se pudo iniciar sesión");
  }
  const data: TokenResponse = await response.json();
  return data.access_token;
}

export function register(email: string, fullName: string, password: string): Promise<User> {
  return apiPost<User>("/users", { email, full_name: fullName, password });
}

export function getCurrentUser(): Promise<User> {
  return apiGet<User>("/users/me");
}
