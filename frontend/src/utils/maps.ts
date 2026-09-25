const GOOGLE_MAPS_HOSTS = new Set(["www.google.com", "google.com", "maps.google.com"]);

// Google blocks framing of regular maps.google.com / maps.app.goo.gl share links.
// Only the official "Embed a map" URL (maps/embed?pb=...) or the no-API-key
// output=embed trick (both produced by the backend's extract_maps_url) can
// actually be shown in an iframe.
export function isEmbeddableMapsLink(url: string): boolean {
  try {
    const parsed = new URL(url);
    if (!GOOGLE_MAPS_HOSTS.has(parsed.hostname)) return false;
    if (parsed.pathname.startsWith("/maps/embed")) return true;
    return parsed.pathname === "/maps" && parsed.searchParams.get("output") === "embed";
  } catch {
    return false;
  }
}
