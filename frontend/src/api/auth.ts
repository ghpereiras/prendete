import { API_URL, ApiError, apiGet, apiPost } from "./client";

export interface User {
  id: number;
  email: string;
  full_name: string;
  avatar_url: string | null;
  created_at: string;
}

interface TokenResponse {
  access_token: string;
  token_type: string;
}

export async function login(email: string, password: string): Promise<string> {
  const body = new URLSearchParams({ username: email, password });
  const response = await fetch(`${API_URL}/auth/login`, {
    method: "POST",
    headers: { "Content-Type": "application/x-www-form-urlencoded" },
    body,
  });
  if (!response.ok) {
    const data = await response.json().catch(() => ({}));
    throw new ApiError(response.status, data.detail ?? "No se pudo iniciar sesión");
  }
  const data: TokenResponse = await response.json();
  return data.access_token;
}

export function register(
  email: string,
  fullName: string,
  password: string,
  avatarBase64?: string | null,
): Promise<User> {
  return apiPost<User>("/users", {
    email,
    full_name: fullName,
    password,
    avatar_base64: avatarBase64 || undefined,
  });
}

export function getCurrentUser(): Promise<User> {
  return apiGet<User>("/users/me");
}
