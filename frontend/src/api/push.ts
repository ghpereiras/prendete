import { apiDelete, apiGet, apiPost } from "./client";

const VAPID_PUBLIC_KEY = import.meta.env.VITE_VAPID_PUBLIC_KEY as string | undefined;

export function isPushSupported(): boolean {
  return "serviceWorker" in navigator && "PushManager" in window;
}

export function registerServiceWorker(): Promise<ServiceWorkerRegistration | null> {
  if (!isPushSupported()) return Promise.resolve(null);
  return navigator.serviceWorker.register("/sw.js");
}

// Web Push wants the VAPID key as a Uint8Array, but env vars are strings.
function urlBase64ToUint8Array(base64String: string): Uint8Array<ArrayBuffer> {
  const padding = "=".repeat((4 - (base64String.length % 4)) % 4);
  const base64 = (base64String + padding).replace(/-/g, "+").replace(/_/g, "/");
  const rawData = atob(base64);
  const bytes = new Uint8Array(new ArrayBuffer(rawData.length));
  for (let i = 0; i < rawData.length; i++) {
    bytes[i] = rawData.charCodeAt(i);
  }
  return bytes;
}

export async function getPushSubscription(): Promise<PushSubscription | null> {
  if (!isPushSupported()) return null;
  const registration = await navigator.serviceWorker.ready;
  return registration.pushManager.getSubscription();
}

// A browser only ever keeps one PushManager subscription per origin. On a
// shared device, whoever last called subscribeToPush() owns it — so a
// subscription existing in the browser doesn't mean it's registered to the
// currently logged-in app user. This checks with the backend to be sure.
export async function getMyPushSubscription(): Promise<PushSubscription | null> {
  const subscription = await getPushSubscription();
  if (!subscription) return null;

  const myEndpoints = await apiGet<string[]>("/users/me/push-subscriptions");
  return myEndpoints.includes(subscription.endpoint) ? subscription : null;
}

export async function subscribeToPush(): Promise<void> {
  if (!VAPID_PUBLIC_KEY) {
    throw new Error("Missing VITE_VAPID_PUBLIC_KEY");
  }

  const permission = await Notification.requestPermission();
  if (permission !== "granted") {
    throw new Error("Notification permission denied");
  }

  const registration = await navigator.serviceWorker.ready;
  const subscription = await registration.pushManager.subscribe({
    userVisibleOnly: true,
    applicationServerKey: urlBase64ToUint8Array(VAPID_PUBLIC_KEY),
  });

  await apiPost("/users/me/push-subscriptions", subscription.toJSON());
}

export async function unsubscribeFromPush(): Promise<void> {
  const subscription = await getPushSubscription();
  if (!subscription) return;
  const endpoint = subscription.endpoint;
  await subscription.unsubscribe();
  await apiDelete(`/users/me/push-subscriptions?endpoint=${encodeURIComponent(endpoint)}`);
}
