export const GOOGLE_CLIENT_ID: string = import.meta.env.VITE_GOOGLE_CLIENT_ID ?? "";

export const GOOGLE_CALLBACK_PATH = "/auth/google/callback";
const PENDING_KEY = "google_signin_pending";

interface PendingSignIn {
  state: string;
  nonce: string;
  returnTo: string;
}

function randomToken(): string {
  const bytes = new Uint8Array(16);
  crypto.getRandomValues(bytes);
  return Array.from(bytes, (b) => b.toString(16).padStart(2, "0")).join("");
}

// Full-page redirect (OIDC implicit flow, id_token only) instead of Google's
// popup button: popups are unreliable in an installed iOS home-screen app.
export function startGoogleSignIn(returnTo: string) {
  const pending: PendingSignIn = { state: randomToken(), nonce: randomToken(), returnTo };
  sessionStorage.setItem(PENDING_KEY, JSON.stringify(pending));

  const params = new URLSearchParams({
    client_id: GOOGLE_CLIENT_ID,
    redirect_uri: `${window.location.origin}${GOOGLE_CALLBACK_PATH}`,
    response_type: "id_token",
    scope: "openid email profile",
    state: pending.state,
    nonce: pending.nonce,
    prompt: "select_account",
  });
  window.location.assign(`https://accounts.google.com/o/oauth2/v2/auth?${params}`);
}

export interface GoogleCallbackResult {
  idToken: string;
  nonce: string;
  returnTo: string;
}

// Returns null if Google reported an error or the state doesn't match the one
// this browser started the sign-in with.
export function readGoogleCallback(hash: string): GoogleCallbackResult | null {
  const raw = sessionStorage.getItem(PENDING_KEY);
  sessionStorage.removeItem(PENDING_KEY);
  if (!raw) return null;

  const pending: PendingSignIn = JSON.parse(raw);
  const params = new URLSearchParams(hash.replace(/^#/, ""));
  const idToken = params.get("id_token");
  if (!idToken || params.get("state") !== pending.state) return null;
  return { idToken, nonce: pending.nonce, returnTo: pending.returnTo };
}
