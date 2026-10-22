# Fix patterns — exact CSS per failure class

Every pattern below removes or re-frames a constraint rather than adding a breakpoint. Prefer them in order.

## 1. Fixed dimension → fluid container

```css
/* before: breaks under 380px */
.card { width: 420px; }

/* after */
.card { width: 100%; max-width: 420px; }
```

```css
/* a grid that fits any width without a media query */
.cards { display: grid; gap: 24px; grid-template-columns: repeat(auto-fit, minmax(min(240px, 100%), 1fr)); }
```

`minmax(min(240px, 100%), 1fr)` is the one-line fix for the classic bug: `minmax(240px, 1fr)` overflows
below 240 px + gutters, and `min()` inside it cannot.

## 2. Rigid row → wrap or stack

```css
.row { display: flex; flex-wrap: wrap; gap: 16px; }
.row > * { flex: 1 1 260px; min-width: 0; }   /* min-width:0 lets flex children shrink */
```

```css
@media (max-width: 640px) {
  .split { grid-template-columns: 1fr; }
  .split .media { order: -1; }   /* image first on phones when it carries the message */
}
```

## 3. Fluid type and spacing

```css
h1 { font-size: clamp(2rem, 1.2rem + 3.6vw, 4.5rem); }
.section { padding-block: clamp(64px, 8vw, 128px); }
.wrap { width: min(100% - 2rem, 1200px); margin-inline: auto; }
```

Body copy never below `1rem` on phones; use `ch` for measure (`max-width: 68ch`), not px; `vw` only inside
`clamp()` so it cannot drop below the floor or blow past the cap.

## 4. Safe areas and viewport units (iOS)

```html
<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">
```

```css
.hero { min-height: 100svh; }          /* small viewport: no jump when the URL bar hides */
.sheet { max-height: 90dvh; }          /* dynamic viewport for modals */
.bottom-bar { position: fixed; inset-inline: 0; bottom: 0;
  padding-bottom: max(12px, env(safe-area-inset-bottom)); }
.page { padding-inline: max(16px, env(safe-area-inset-left)) max(16px, env(safe-area-inset-right)); }
```

## 5. Inputs that do not trigger the iOS zoom

```css
input, select, textarea, button { font-size: max(16px, 1rem); }
```

Pairs with `inputmode`, `enterkeyhint`, `autocomplete` — the right keyboard is part of responsiveness.

## 6. Tap targets without changing the visual

```css
.icon-btn { position: relative; }
.icon-btn::after { content: ''; position: absolute; inset: -10px; }   /* 28px glyph → 48px hit area */
```

## 7. Tables on phones

```css
.table-scroll { overflow-x: auto; -webkit-overflow-scrolling: touch; }
```

Scrolling a table inside its own container is sanctioned (WCAG 1.4.10 permits 2-D layout for data tables).
Scrolling the whole page is not.

```css
@media (max-width: 640px) {
  table, thead, tbody, tr, th, td { display: block; }
  thead { display: none; }
  td::before { content: attr(data-label); display: block; font-size: .75rem; opacity: .7; }
}
```

## 8. Sticky and fixed chrome

`position: sticky` over `fixed` where possible; cap the header at ~15% of viewport height under 480 px;
collapse nav into a menu rather than wrapping to three rows; drop decorative side rails under 900 px; drop
`backdrop-filter` on large fixed surfaces at phone widths.

---

# Wide-screen patterns (1440 → 3840)

The wide end fails because nothing forces a decision. These are the decisions.

## 9. Readable measure, independent of the grid

```css
.prose { max-width: 68ch; }                 /* ≈ 65–75 characters: comfortable */
p, li, blockquote { max-width: 72ch; }
.prose > * { max-width: 100%; }
```

Measure in `ch`, never px — `ch` follows the font, so a larger root size keeps the character count. For
CJK halve it (`max-width: 34em` reads as ~40 glyphs).

## 10. Prose narrow, catalogue wide — two ceilings, not one

```css
:root { --wrap-prose: 72rem; --wrap-wide: 96rem; }
.section--prose { max-width: var(--wrap-prose); }
.section--catalogue { max-width: var(--wrap-wide); }
```

A single global `max-width: 1200px` is the most common wide-screen failure: right for a paragraph, wrong
for a 4-column product grid on a 3440 px display.

## 11. Density that grows with the display

```css
.grid { display: grid; gap: clamp(16px, 1.2vw, 32px);
  grid-template-columns: repeat(auto-fit, minmax(min(320px, 100%), 1fr)); }
@media (min-width: 1600px) { .grid { grid-template-columns: repeat(auto-fit, minmax(min(380px, 100%), 1fr)); } }
```

`auto-fit` alone already adds columns; the media query only widens the minimum so cards do not become
700 px of empty air.

## 12. Type that keeps scaling, with a stop

```css
body { font-size: clamp(1rem, 0.95rem + 0.15vw, 1.125rem); }
h1   { font-size: clamp(2.5rem, 1.6rem + 2.8vw, 5.5rem); }
```

Uncapped `vw` type becomes billboard lettering at 3440. Always cap the third term.

## 13. Pixels that survive a 4K display

```html
<img src="logo-2x.png" srcset="logo-2x.png 2x" width="240" height="64" alt="…">
```

```css
img { max-width: 100%; height: auto; }         /* never stretch past natural size */
.hero img { width: min(100%, 1200px); }          /* cap before it upscales */
```

A block logo rendered at 240 CSS px on a 2× screen needs 480 device pixels; below that it is soft, which
reads as low quality even when the layout is perfect.

## 14. Chrome that expands instead of hiding

```css
@media (min-width: 1024px) {
  .nav-toggle { display: none; }
  .nav-links { display: flex; }        /* a desktop keeps a real nav */
}
```

## 15. Container-driven components (the modern default)

```css
.card-host { container-type: inline-size; }
@container (min-width: 480px) { .card { grid-template-columns: 120px 1fr; } }
```

Container queries beat viewport queries for components that get reused at different widths — a card in a
sidebar and the same card in a full-width grid need different layouts at the same viewport.

## 16. Intentional wide composition, when the content is thin

If a page genuinely has little content, do not stretch it — compose: a wide hero with the headline locked
to the left third and the image bleeding right; a full-width band with an inset text well
(`padding-inline: max(24px, calc((100% - 72ch)/2))`). Dead space is fine when it is *designed*; it is a
bug when it is a 1200 px column with `margin: auto` and nothing else.
