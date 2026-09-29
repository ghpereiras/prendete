import type { Language } from "../i18n";
import { API_URL, ApiError, apiGet, apiPatch, apiPost } from "./client";

export interface User {
  id: number;
  email: string;
  first_name: string;
  last_name: string;
  full_name: string;
  language: Language;
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
  firstName: string,
  lastName: string,
  password: string,
  language: Language,
  avatarBase64?: string | null,
): Promise<User> {
  return apiPost<User>("/users", {
    email,
    first_name: firstName,
    last_name: lastName,
    password,
    language,
    avatar_base64: avatarBase64 || undefined,
  });
}

export function getCurrentUser(): Promise<User> {
  return apiGet<User>("/users/me");
}

export interface ProfileUpdate {
  firstName?: string;
  lastName?: string;
  language?: Language;
  avatarBase64?: string;
  removeAvatar?: boolean;
}

export function updateProfile(update: ProfileUpdate): Promise<User> {
  return apiPatch<User>("/users/me", {
    first_name: update.firstName,
    last_name: update.lastName,
    language: update.language,
    avatar_base64: update.avatarBase64,
    remove_avatar: update.removeAvatar ?? false,
  });
}
