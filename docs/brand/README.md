# Prendete brand

Open [brand-board.html](brand-board.html) in a browser for the visual guide. The SVG files are the source of truth; the PNGs in `png/` are exported from them.

## Strategy

- **What it is:** an app to organize plans among friends: an event with an invite link and attendance, or a poll to find the date that works for everybody. No chat, no ticketing.
- **Who it's for:** friend groups in Argentina and Latin America, roughly 20 to 35. Mobile first, informal tone (voseo).
- **What it competes with:** the chaos of a WhatsApp group trying to agree on a plan.
- **The brand idea:** the name already is the campaign. *"¿Te prendés?"* is literally how an Argentine invites you to a plan, and *prender* also means to switch on. So **the p of the name lights up**.
- **Where recognition happens:** on the home-screen icon and in the preview of every shared link — a small square. That's why the system is a strong wordmark whose first letter is also the icon, instead of a separate symbol that needs explaining.

## The system

- **Wordmark:** "prendete" in Fredoka SemiBold, with the counter of the p filled with amber light. Violet on light backgrounds is the primary version; white on violet or dark.
- **App icon:** the lit p alone, white on violet. Same glyph, same light, so the icon and the name reinforce each other.
- **One ink:** the wordmark with the counter left open, for single-color uses.
- **Voice:** "¿Te prendés?" as the headline for invites and campaigns.

## Typeface

**Fredoka SemiBold** (SIL Open Font License 1.1), tracking −0.6% on top of the font's own kerning. The letters are converted to outlines in the SVGs, so the logo doesn't depend on having the font installed. If the UI ever adopts it for headings, it can be loaded from Google Fonts.

Shortlisted from eight candidates (Fredoka, Nunito, Baloo 2, Rubik, Outfit, Gabarito, Bricolage Grotesque, Plus Jakarta Sans), with the final three tested with the full system applied:

- **Fredoka** (chosen): round and warm; it is the one that sounds like a get-together, informal without being childish. Its generous, round counter makes the light read as a light.
- **Bricolage Grotesque:** the most character, but its narrow counter turns the light into a squeezed oval.
- **Outfit:** the cleanest, but generic: the look of a thousand startups.

## Previous attempts, and why they were dropped

- **A hand-drawn monoline wordmark:** poor letter spacing and legibility. A brand needs a professional typeface with designed kerning.
- **A chat bubble with three dots:** it reads as messaging, and Prendete has no chat.
- **Three overlapping circles with a lit core:** explainable but not memorable; no brand appeal.
- **A ticket, a calendar page, a ring of dots, a lightning bolt, a sparkle star:** respectively ticketing, generic, illegible when small, and overused.

## Palette

The previous UI colors (`#aa3bff`, `#c084fc`, `#16171d`) and the old icon came from the Vite project template, so violet and black were never a brand decision.

- **Violet stays as the brand color.** It reads as creative and social, and it is less crowded than the oranges and reds of the event category, so it differentiates.
- **Black is not a brand color.** It is fine as the app's dark theme, but a logo that only lives on black reads as nightlife or developer tooling.
- **One warm accent, used once:** amber, the complement of violet, only inside the p.
- **Accessibility:** the template accent `#aa3bff` on white is 4.39:1 and fails the 4.5:1 minimum for text; `#7B3FF2` on paper is 5.2:1.

| Token | Hex | Use | Contrast |
| --- | --- | --- | --- |
| Prendete violet | `#7B3FF2` | Primary, the wordmark on light | white on it 5.5:1; on paper 5.2:1 |
| Deep violet | `#5B21D6` | Backgrounds, buttons | white on it 8.0:1 |
| Light violet | `#A579FF` | Accents on dark | on ink 5.8:1 |
| Spark | `#FFB020` | Only inside the p | never text |
| Ink | `#16171D` | Dark background, text | on paper 17:1 |
| Paper | `#FAF8FF` | Light background | |

## Files

| File | Use |
| --- | --- |
| `logo-violet.svg`, `png/logo-violet-1600.png` | Primary wordmark, for light backgrounds |
| `logo-white.svg`, `png/logo-white-1600.png` | For violet or dark backgrounds |
| `logo-ink.svg`, `png/logo-ink-1600.png` | When color isn't possible |
| `logo-mono.svg` | One ink (`currentColor`), counter open |
| `symbol.svg`, `png/symbol-512.png` | The lit p alone, transparent background |
| `app-icon.svg`, `png/app-icon-{512,192,180}.png` | App and home-screen icon (full bleed; the OS rounds the corners) |
| `app-icon-maskable.svg`, `png/app-icon-maskable-512.png` | Android adaptive icon |
| `favicon.svg` | Browser tab icon (rounded tile) |

## Using it in the app

Not applied yet. To adopt it: copy `favicon.svg` and the `app-icon-*.png` files over `frontend/public/` (`icon-180.png`, `icon-192.png`, `icon-512.png`), add the maskable icon to `manifest.json` with `"purpose": "maskable"`, move the light-mode UI accent to `#7B3FF2`, and regenerate the link-preview images (`frontend/public/og-image.jpg`, `docs/social-preview.jpg`). The leftover `frontend/public/icons.svg` is the template's social-icons sprite and is unused.
