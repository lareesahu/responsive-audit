# iOS / mobile traps that emulation will not tell you about

Chrome device emulation proves layout geometry. These behaviours are Safari- or OS-specific and must be
reasoned about, or tested on a real device, and reported as unverified when neither happens.

## Rendering and viewport

1. `100vh` is the *large* viewport in Safari — heroes are cut on first paint. Use `100svh` (fits now) and
   `100dvh` (resizes with the toolbar).
2. The URL bar hides on scroll, so anything anchored with `vh` shifts by ~60–100 px mid-scroll. Prefer
   `svh` for above-the-fold height and `dvh` for overlays.
3. `viewport-fit=cover` is required for `env(safe-area-inset-*)` to report real values; without it they are 0.
   Notched phones need bottom padding on fixed bars (34 px) and side padding in landscape (44 px).
4. `-webkit-fill-available` is still needed for some full-height children inside flex; `height: 100%`
   alone can collapse.
5. `overflow: hidden` on `html`/`body` in Safari can block momentum scrolling on descendants; use
   `overscroll-behavior` instead when you mean "stop chaining".

## Keyboard and focus

6. Any input with `font-size < 16px` triggers an automatic zoom on focus, and the page stays zoomed. Fix the
   font size; do not disable zoom in the viewport meta (that breaks accessibility).
7. The keyboard shrinks the *visual* viewport but not `window.innerHeight`. Listen to
   `window.visualViewport` (`resize`, `offsetTop`) if a bottom-anchored composer or CTA must stay visible.
8. Inputs need `inputmode` (numeric, tel, email, decimal) or users get the wrong keyboard — a functional
   responsiveness failure.
9. `position: fixed` elements inside a transformed ancestor stop being fixed. Check for `transform`,
   `filter`, `will-change` up the tree.

## Touch and interaction

10. Hover-only affordances do not exist on phones. Any `:hover`-revealed action needs a visible tap
    equivalent, and any hover-expanded menu needs a touch path.
11. Targets must be ≥ 44 × 44 px (Apple HIG); WCAG 2.5.8 sets 24 × 24 px as the hard minimum. Pad the hit
    area, never the icon.
12. Double-tap-to-zoom is triggered by `touch-action: manipulation` on rapid taps in some layouts; set it
    on controls you do not want to zoom.
13. `100%` width plus `padding` on a flex child overflows unless `box-sizing: border-box` is global and the
    child has `min-width: 0`.
14. Rubber-band scroll at the end of a page reveals the body background — a dark page on a white body looks
    broken. Set the body/`html` background to the page's base colour.

## Text and zoom

15. `-webkit-text-size-adjust: 100%` prevents Safari inflating text on rotation in landscape.
16. iOS honours user text-size settings: test with larger text if the design uses fixed heights on text
    blocks; use `min-height` not `height`.
17. `line-height` with fixed px on fluid type causes overlap at small sizes; use unitless line-height.

## What to write in the report

When a page passes in emulation but has not been on a device, the honest line is:

> Responsive gate: 320 ✓ 375 ✓ 390 ✓ 430 ✓ 768 ✓ 1024 ✓ 1440 ✓ — Chrome emulation; Safari behaviour
> unverified (no device in this session).
