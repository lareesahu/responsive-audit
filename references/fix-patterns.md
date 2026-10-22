# Fix patterns — exact CSS per failure class

Every pattern below removes a constraint rather than adding a breakpoint. Prefer them in order.

## 1. Fixed dimension → fluid container

```css
/* before: breaks under 380px */
.card { width: 420px; }

/* after */
.card { width: 100%; max-width: 420px; }
```

```css
/* grid that fits any width without a media query */
.cards { display: grid; gap: 24px; grid-template-columns: repeat(auto-fit, minmax(min(240px, 100%), 1fr)); }
```

`minmax(min(240px, 100%), 1fr)` is the one-line fix for the classic bug: `minmax(240px, 1fr)`
overflows below 240 px + gutters, and `min()` inside it cannot.

## 2. Rigid row → wrap or stack

```css
.row { display: flex; flex-wrap: wrap; gap: 16px; }
.row > * { flex: 1 1 260px; min-width: 0; }   /* min-width:0 lets flex children shrink */
```

```css
/* explicit stack when the pairing is intentional */
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

Rules: never `font-size` below `1rem` for body copy on phones; use `ch` for measure
(`max-width: 68ch`), not px; use `vw` only inside `clamp()` so it cannot go below the floor.

## 4. Safe areas and viewport units (iOS)

```html
<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">
```

```css
.hero { min-height: 100svh; }          /* small viewport: no jump when the URL bar hides */
.sheet { max-height: 90dvh; }          /* dynamic viewport for modals */
.bottom-bar {
  position: fixed; inset-inline: 0; bottom: 0;
  padding-bottom: max(12px, env(safe-area-inset-bottom));
}
.page { padding-inline: max(16px, env(safe-area-inset-left)) max(16px, env(safe-area-inset-right)); }
```

`100vh` on iOS is the *large* viewport height, so fixed-height heroes get cut by the toolbar. Use
`svh` for anything that must fully fit on first paint, `dvh` for things that may resize.

## 5. Inputs that do not trigger the iOS zoom

```css
input, select, textarea, button { font-size: max(16px, 1rem); }
```

Also: `enterkeyhint`, `inputmode`, `autocomplete` — a numeric field with `inputmode="numeric"` prevents
the wrong keyboard, which is a responsiveness failure users feel.

## 6. Tap targets without changing the visual

```css
.icon-btn { position: relative; }
.icon-btn::after { content: ''; position: absolute; inset: -10px; }   /* 28px glyph → 48px hit area */
```

Targets inside dense rows: increase row height and `gap`, never shrink the glyph.

## 7. Tables on phones

```css
.table-scroll { overflow-x: auto; -webkit-overflow-scrolling: touch; }
```

Scrolling a table inside its own container is sanctioned (WCAG 1.4.10 permits two-dimensional layout for
data tables). Scrolling the whole page is not. If the table is small, the better answer is stacking:

```css
@media (max-width: 640px) {
  table, thead, tbody, tr, th, td { display: block; }
  thead { display: none; }
  td::before { content: attr(data-label); display: block; font-size: .75rem; opacity: .7; }
}
```

## 8. Sticky and fixed chrome

Rules that keep headers from eating the phone: `position: sticky` over `fixed` whenever possible; cap the
header at ~15% of viewport height under 480 px; collapse nav into a menu rather than wrapping to three
rows; drop decorative side rails under 900 px; and drop `backdrop-filter` blurs on large fixed surfaces at
phone widths (they cost frames and look like fog on small screens).

## 9. Hide is not a narrow-width behaviour

`display: none` on phone removes information. If something genuinely cannot fit, replace it with a
compact variant (icon-only button with an accessible name, a summary line, an expandable disclosure) and
say so in the report.
