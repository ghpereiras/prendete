export function isIos(): boolean {
  const ua = window.navigator.userAgent;
  const isAppleMobile = /iPad|iPhone|iPod/.test(ua);
  // iPadOS 13+ reports its UA as "Macintosh" — maxTouchPoints tells it apart from a real Mac.
  const isTouchMac = /Macintosh/.test(ua) && navigator.maxTouchPoints > 1;
  return isAppleMobile || isTouchMac;
}

export function isStandalone(): boolean {
  const nav = window.navigator as Navigator & { standalone?: boolean };
  return window.matchMedia("(display-mode: standalone)").matches || nav.standalone === true;
}
