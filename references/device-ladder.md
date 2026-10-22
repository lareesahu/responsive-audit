# Device ladder — what to actually test

Widths in CSS pixels. Test the ladder, not one phone. The number that matters is the narrowest,
not the newest.

## Default ladder (web)

| Width | Represents | Why it is on the list |
|---|---|---|
| **320** | iPhone SE 1st gen, WCAG reflow floor, 1280 px at 400% zoom | Hard floor. If it fails here it fails the accessibility criterion. |
| **375** | iPhone SE 2/3, iPhone 13 mini | The smallest phone most people still hold. |
| **390** | iPhone 12/13/14 | The modal iPhone size — always screenshot this one. |
| **393** | iPhone 15/16 | Current baseline. |
| **402** | iPhone 16 Pro | Slightly wider; catches rules keyed to exactly 390. |
| **430** | iPhone 15/16 Pro Max | Largest phone; catches rules keyed to `max-width: 400px`. |
| **768** | iPad portrait | The transition: rows want to become columns here. |
| **834 / 1024** | iPad landscape, small laptop | Where sticky sidebars and 2-column heroes usually break. |
| **1280** | Laptop | Default desktop design width. |
| **1440** | Desktop | Delivery screenshot width. |
| **1920+** | Wide monitor | Catches unbounded line lengths and content stranded at `max-width` edges. |

Minimum gate: **320, 375, 390, 430, 768, 1024, 1440**. Add 402 when the design uses hard phone
breakpoints, and 1920 when there is a hero or a full-bleed band.

## Height also matters

- **Phone 844** — iPhone 12–16 default.
- **Phone 667** — iPhone SE, no notch; bottom bars lose their safe area and heroes get clipped.
- **Phone 700 with the URL bar showing** — this is what users actually see before scrolling.
- **Landscape 390 × 844** — a 390 px tall viewport defeats `100vh` heroes and fixed modals.

## Orientation and zoom

- Rotate phones once: sticky headers, `min-height: 100vh` heroes and full-screen modals fail in landscape
  more often than in portrait.
- 400% zoom at 1280 px = 320 CSS px. Same test as the narrowest phone, different cause.
- Large text / 200% font: test with the browser's text-only zoom if the layout uses fixed line heights.

## App targets (installed web apps, Electron, React Native web views)

Add the specific window sizes the shell enforces, because a desktop app window can be narrower than a
phone in pixels:

- Side-by-side split at 720 and 560 px.
- Browser tab at 500 and 380 px.
- The app's own minimum window width (read `minWidth` in Electron config or `min-width` in the shell CSS)
  — if the app prevents resizing below 800 px, the layout only needs to survive 800, and saying so is part
  of the audit.

## What each width check must produce

1. No horizontal scrollbar (`scrollWidth` ≤ `innerWidth`).
2. No element crossing either edge.
3. No text clipped by a fixed height.
4. Every interactive target ≥ 44 px, never < 24 px.
5. Body text ≥ 16 px, inputs ≥ 16 px.
6. A screenshot at that width, full page, reviewed by eye at least at 320, 390, 768 and 1440.
