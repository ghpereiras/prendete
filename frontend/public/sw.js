// Activate a new version of this file immediately instead of waiting for
// every open tab to close — otherwise a fix like the notificationclick one
// below wouldn't take effect until the user fully closes the browser.
self.addEventListener("install", () => {
  self.skipWaiting();
});

self.addEventListener("activate", (event) => {
  event.waitUntil(self.clients.claim());
});

self.addEventListener("push", (event) => {
  let data = {};
  try {
    data = event.data ? event.data.json() : {};
  } catch {
    data = { body: event.data ? event.data.text() : "" };
  }

  const title = data.title || "Prendete";
  const options = {
    body: data.body || "",
    icon: "/favicon.svg",
    data: { url: data.url || "/" },
  };

  event.waitUntil(self.registration.showNotification(title, options));
});

self.addEventListener("notificationclick", (event) => {
  event.notification.close();
  const url = event.notification.data?.url || "/";
  const targetUrl = new URL(url, self.location.origin).href;

  event.waitUntil(
    self.clients.matchAll({ type: "window", includeUncontrolled: true }).then((clientList) => {
      // Reusing an already-open tab in place needs WindowClient.navigate(),
      // which is unreliable across browsers for navigating into an SPA route
      // (it can hang indefinitely instead of resolving). Only reuse a tab
      // that's already showing this exact URL (a plain focus, no navigation);
      // otherwise always open a fresh tab, which is consistently reliable.
      for (const client of clientList) {
        if (client.url === targetUrl && "focus" in client) {
          return client.focus();
        }
      }
      return self.clients.openWindow(targetUrl);
    }),
  );
});
