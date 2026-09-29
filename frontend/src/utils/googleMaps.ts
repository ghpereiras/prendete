let loadPromise: Promise<typeof google> | null = null;

// Loads the Maps JavaScript API (+ Places library) exactly once, regardless
// of how many components ask for it.
export function loadGoogleMaps(): Promise<typeof google> {
  if (loadPromise) return loadPromise;

  const apiKey = import.meta.env.VITE_GOOGLE_MAPS_API_KEY as string | undefined;
  if (!apiKey) {
    return Promise.reject(new Error("VITE_GOOGLE_MAPS_API_KEY is not set"));
  }

  loadPromise = new Promise((resolve, reject) => {
    if (window.google?.maps) {
      resolve(window.google);
      return;
    }

    const callbackName = "__prendete_google_maps_loaded";
    (window as unknown as Record<string, () => void>)[callbackName] = () => resolve(window.google);

    const script = document.createElement("script");
    script.src = `https://maps.googleapis.com/maps/api/js?key=${apiKey}&libraries=places&loading=async&callback=${callbackName}`;
    script.async = true;
    script.onerror = () => reject(new Error("Failed to load Google Maps"));
    document.head.appendChild(script);
  });

  return loadPromise;
}

export function buildEmbedUrl(placeId: string): string {
  const apiKey = import.meta.env.VITE_GOOGLE_MAPS_API_KEY as string;
  return `https://www.google.com/maps/embed/v1/place?key=${apiKey}&q=place_id:${placeId}`;
}
