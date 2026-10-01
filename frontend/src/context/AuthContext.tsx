import { createContext, useContext, useEffect, useState, type ReactNode } from "react";
import {
  getCurrentUser,
  login as apiLogin,
  loginWithGoogle as apiLoginWithGoogle,
  updateProfile as apiUpdateProfile,
  type ProfileUpdate,
  type User,
} from "../api/auth";
import i18n, { type Language } from "../i18n";

// The account's saved language is the source of truth once logged in (it's
// what backend push notifications are rendered in too) — apply it so the UI
// matches, even if this browser had a different language selected before.
function syncLanguage(user: User) {
  if (user.language && user.language !== i18n.resolvedLanguage) {
    i18n.changeLanguage(user.language);
  }
}

interface AuthContextValue {
  user: User | null;
  loading: boolean;
  login: (email: string, password: string) => Promise<void>;
  loginWithGoogle: (credential: string, nonce: string) => Promise<void>;
  logout: () => void;
  updateProfile: (update: ProfileUpdate) => Promise<void>;
}

const AuthContext = createContext<AuthContextValue | undefined>(undefined);

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<User | null>(null);
  const [loading, setLoading] = useState(true);

  function applyUser(loadedUser: User) {
    syncLanguage(loadedUser);
    setUser(loadedUser);
    return loadedUser;
  }

  useEffect(() => {
    const token = localStorage.getItem("access_token");
    if (!token) {
      setLoading(false);
      return;
    }
    getCurrentUser()
      .then(applyUser)
      .catch(() => localStorage.removeItem("access_token"))
      .finally(() => setLoading(false));
  }, []);

  useEffect(() => {
    // Another tab logged in/out (localStorage is shared per-origin); reload
    // so this tab picks up the new session instead of showing a stale user.
    function handleStorage(e: StorageEvent) {
      if (e.key === "access_token") {
        window.location.reload();
      }
    }
    window.addEventListener("storage", handleStorage);
    return () => window.removeEventListener("storage", handleStorage);
  }, []);

  async function login(email: string, password: string) {
    const token = await apiLogin(email, password);
    localStorage.setItem("access_token", token);
    applyUser(await getCurrentUser());
  }

  async function loginWithGoogle(credential: string, nonce: string) {
    const token = await apiLoginWithGoogle(credential, nonce, i18n.resolvedLanguage as Language);
    localStorage.setItem("access_token", token);
    applyUser(await getCurrentUser());
  }

  function logout() {
    localStorage.removeItem("access_token");
    setUser(null);
  }

  async function updateProfile(update: ProfileUpdate) {
    applyUser(await apiUpdateProfile(update));
  }

  return (
    <AuthContext.Provider value={{ user, loading, login, loginWithGoogle, logout, updateProfile }}>
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth(): AuthContextValue {
  const ctx = useContext(AuthContext);
  if (!ctx) {
    throw new Error("useAuth must be used within an AuthProvider");
  }
  return ctx;
}
