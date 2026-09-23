// Google blocks framing of regular maps.google.com / maps.app.goo.gl share links.
// Only the "Embed a map" URL (maps/embed?pb=...) can actually be shown in an iframe.
export function isEmbeddableMapsLink(url: string): boolean {
  try {
    const parsed = new URL(url);
    const isGoogleHost = parsed.hostname === "www.google.com" || parsed.hostname === "google.com";
    return isGoogleHost && parsed.pathname.startsWith("/maps/embed");
  } catch {
    return false;
  }
}
