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

// Touch devices synthesize a hover/mouseenter event right before a tap's click
// event, so a dropdown trigger that opens on hover can't tell "the pointer is
// hovering" apart from "the user just tapped" — checking this lets us only
// wire up hover-to-open on devices with a real mouse, where that ambiguity
// doesn't exist.
export function supportsHover(): boolean {
  return window.matchMedia("(hover: hover) and (pointer: fine)").matches;
}
