---
name: responsive-audit
description: Use when auditing or fixing an app's responsiveness.
version: 2.1.0
author: Lareesa Hu (Pulse Branding), built with Hermes
license: MIT
metadata:
  hermes:
    icon: lucide:monitor-smartphone
    tags:
    - Frontend
    - Responsive
    - Mobile
    - Wide
    - Audit
---

# Responsive audit

A layout is responsive when it holds at **320 CSS pixels** and at **3440** — the narrowest phone in
reflow, and the widest display anyone actually uses. Both ends are the same problem seen from opposite
sides: a good layout has no hard constraints, so shrinking removes width and growing adds it, without
losing content, function or legibility.

## When to Use

Load this skill when any of these is true:

- Someone says the app or page is broken, cramped, cut off, stretched, or "weird" on a phone, a laptop,
  an ultrawide monitor, or in a split window.
- A UI change is about to ship and layout must be checked across the range, not at one size.
- A new page, component, modal, table, nav or form is being added and its narrow- **and** wide-width
  behaviour is undefined.
- The user asks for a responsive, mobile, breakpoint, viewport, wide-screen, or device-compatibility review.
- A build runs in a resizable desktop shell (Electron, browser window, split view, iPad multitasking, Slide
  Over) where the window can be narrower than a phone or wider than the design's max width.

Do not load it for pure visual/style direction (use `ui-ux-pro-max`) or for spacing and build standards
(use `frontend-ui-engineering`).

## The foundational principle

> **Responsive layout is the absence of fixed constraints, not the presence of breakpoints.**
> Every dimension is either intrinsic (content decides), relative (`%`, `fr`, `vw` inside `clamp()`),
> or bounded (`min()` / `max()`). Any hard `width`, `min-width`, `height`, or absolutely positioned
> column is a decision that the layout must eventually break at some viewport — narrow *or* wide.

Four consequences, and every rule in this skill falls out of them:

1. **Width belongs to the content**, so resizing removes or adds width, never content. There are exactly
   four sanctioned behaviours at any width: **reflow** (stack), **scroll inside its own container**,
   **shrink or grow to a floor/ceiling**, or **replace with a compact/roomy variant**. A fifth behaviour —
   silently clipping, hiding, or overflowing — is a bug, always.
2. **The narrowest real target is the floor**, so build down from 320 px, not down from a desktop
   screenshot. WCAG 2.2 SC 1.4.10 requires no two-dimensional scrolling at 320 CSS px (= 1280 px at 400%
   zoom).
3. **The widest real target is the ceiling**, and it is not "the same layout, centred". Past ~1440 px a
   layout must make new decisions: measure, columns, density, image resolution, and where the eye lands.
   A page that looks identical at 1440 and 3440 has stopped responding at the exact width it has most room.
4. **Legibility and touch have floors and ceilings that layout may not cross**: body text ≥ 16 px on
   phones; form inputs ≥ 16 px (below that iOS Safari zooms on focus); interactive targets ≥ 44 × 44 px
   (Apple HIG) and never below 24 × 24 px (WCAG 2.5.8); a line of text ≤ 80 characters (≤ 40 for CJK,
   WCAG 1.4.8) no matter how wide the window gets.

Device lists are a checklist of *places to look*, never the design target. If the layout is correct by
construction, every width between 320 and 3840 passes without a new breakpoint.

## The two ends, and why they fail differently

**Narrow end (320–430).** Content is squeezed out: rigid rows overflow, fixed widths force a sideways
scroll, text clips, targets get too small, and `100vh` jumps with the browser bar.

**Wide end (1440–3840).** Room is wasted or misused: a 1200 px column floats in 1300 px of margin, a line
of text runs 140 characters, a 900 px photo is stretched to 2400 px and turns to mush, a card grid stays
three-wide while each card becomes 500 px of empty air, and the nav still hides behind a hamburger on a
27-inch display. None of these break a box measurement — which is why a mobile-only audit passes them.

| Wide failure | What it looks like | Fix |
|---|---|---|
| **Unbounded measure** | paragraph lines of 120+ characters | `max-width: 68ch` on prose, or `min(72ch, 100%)` |
| **Plateau** | content identical at 1440 and 2560, huge dead margins | let the grid take columns (`auto-fit`), or raise the ceiling per page type |
| **Starved columns** | 3 cards, each 700 px wide with a sentence in them | `repeat(auto-fit, minmax(min(340px,100%),1fr))`, cap card width, add a sidebar |
| **Upscaled pixels** | logo/photo blurry on a 4K screen | `srcset`/`image-set()` at 2×, or cap the render width |
| **Phone chrome at desk size** | hamburger nav on 2560, mobile accordions in 3 columns of unused space | expand to a real nav and persistent side rails at `≥1024` |
| **Type that stops scaling** | 14 px body at 3440 next to a 120 px headline | `clamp()` scale with a vw term and a cap |

## Standards this encodes

| Source | Rule used here |
|---|---|
| [WCAG 2.2 SC 1.4.10 Reflow](https://www.w3.org/WAI/WCAG22/Understanding/reflow.html) | No 2-D scrolling at 320 CSS px / 400% zoom — the narrow floor |
| [WCAG 2.2 SC 1.4.8 Visual Presentation](https://www.w3.org/WAI/WCAG22/Understanding/visual-presentation.html) | Lines ≤ 80 characters, ≤ 40 for CJK — the measure ceiling |
| [WCAG 2.2 SC 2.5.8 Target Size](https://www.w3.org/WAI/WCAG22/Understanding/target-size-minimum.html) | Targets ≥ 24 × 24 px minimum |
| [Apple HIG — Layout](https://developer.apple.com/design/human-interface-guidelines/layout) | Adapt to size classes and window configurations; layout guides "restrict the width of text for optimal readability"; preview the **largest and smallest** layouts |
| [Apple `readableContentGuide`](https://developer.apple.com/documentation/uikit/uiview/readablecontentguide) | Readable width is a first-class constraint, not an accident of the grid |
| [Android / Material window size classes](https://developer.android.com/develop/ui/compose/layouts/adaptive/use-window-size-classes) | compact < 600, medium 600–839, expanded 840–1199, large 1200–1599, extra-large ≥ 1600 — the width ladder used below |
| [MDN — viewport units](https://developer.mozilla.org/en-US/docs/Web/CSS/length) | `svh`/`dvh`/`lvh` exist because `vh` lies on mobile |

Apple's own testing rule is the one to copy: *preview the largest and the smallest layouts first* — they
fail for different reasons, and the middle sizes almost always inherit whichever ones you fix.

## Workflow

Public source of this skill: <https://github.com/lareesahu/responsive-audit> (MIT). If the local copy and
the repo disagree, the repo is canonical — pull it rather than editing a stale copy.

### 1. Establish the target
Name the app, the URL or file, the build (branch/commit or port), and the viewport plan. Read the project's
own conventions first (`AGENTS.md`, design tokens, existing breakpoints) so fixes reuse the house scale
instead of inventing values. Default ladder and the window-size classes: `references/device-ladder.md`.

### 2. Run the measurable audit

```bash
python scripts/responsive_audit.py --url http://127.0.0.1:5173 --out ./audit          # full ladder
python scripts/responsive_audit.py --url https://site.com --devices iphone           # phones only
python scripts/responsive_audit.py --url https://site.com --devices wide             # 1440 → 3440
python scripts/responsive_audit.py --url https://site.com --devices full             # 320 → 2560
```

It loads the page at every width, scrolls it to trigger lazy content, then traces real geometry:
horizontal overflow and which element causes it, text clipped by fixed heights, targets under 44 px,
inputs that trigger iOS zoom, images distorted by `object-fit: fill` **or upscaled past their natural
width**, characters per line measured from actual line boxes, how much of a wide viewport the content
actually uses, and tiny type. It writes screenshots plus a JSON report and exits non-zero when the gate
fails.

Never substitute "I looked at a screenshot" for this run. Screenshots prove appearance; the script proves
geometry.

### 3. Classify, then fix by pattern
Each finding belongs to one of the classes above. Fix the class, not the instance — one fixed `width`
usually means eight more like it, and patching only the one you saw is how a page passes today and breaks
next week.

| Class | Symptom | Fix pattern |
|---|---|---|
| Fixed dimension | `scrollWidth > innerWidth`, element crossing an edge | `max-width` + `%`, `minmax()`, `flex: 1 1 auto`, `clamp()` |
| Rigid row | Side-by-side blocks that cannot fit | `auto-fit`/`minmax()`, `flex-wrap`, stack under 640 px |
| Clipped content | Text cut, truncation with no alternative | remove fixed `height`, use `min-height`; if truncation is intended, give a disclosure |
| Touch/type floor | Target < 44 px, input < 16 px, body < 16 px | pad the hit area, `font-size: max(16px, 1rem)` |
| Viewport unit abuse | jumps with the iOS URL bar, content behind the home indicator | `100dvh`/`100svh`, `env(safe-area-inset-*)` |
| Wide plateau | identical layout at 1440 and 2560 | add columns/density at `≥1600`; keep prose at `≤72ch` |
| Wide measure | 100+ characters per line | `max-width: 68ch` on `p`, `li`, `blockquote` |
| Wide pixels | blurry logo or photo at 2× | `srcset` 2×, or `max-width` matching the asset |

Exact CSS for each: `references/fix-patterns.md`. iOS traps emulation cannot see: `references/ios-checklist.md`.

### 4. Verify, then report
Re-run until every width passes, then look at the four screenshots that matter with your own eyes —
**320, 390, 768, 1440, plus one wide frame (1920 or 2560)** — before claiming anything. A passing script
with an ugly phone layout, or a tidy phone page that turns into a narrow ribbon on a 27-inch display, is a
fail: geometry is the floor, not the standard.

### 5. The ceiling pass (a green gate is not a verdict)

The gate above is the floor: nothing is broken. It is not the deliverable. Before reporting, compare the
page against the best version of its own kind and close what you can:

| Page type | The ceiling looks like |
|---|---|
| Marketing / landing | a hero that uses the display at 2560, not a 1200 px column with margins; type that scales; imagery that stays sharp |
| Editorial / prose | 65–75 characters per line at every width, a calm measure, deliberate rather than default whitespace |
| Catalogue / dashboard | density that grows with the display (`auto-fit` plus a wider minimum), no 700 px cards holding one sentence |
| App shell | persistent nav and side rails at ≥ 1024, no hamburger on a desktop |

State which rows you checked and what remains below the ceiling. "Passes at every width" is a floor
sentence; the report says how good it is, and what still falls short.

Report as: what failed, what class it belonged to, what changed, the gate line
`Responsive gate: 320 ✓ 375 ✓ 390 ✓ 430 ✓ 768 ✓ 1024 ✓ 1440 ✓ 1920 ✓ 2560 ✓`, then the one-line
ceiling verdict — what it is measured against and what is still short.

## What this skill is not

- It does not choose the visual direction. Load `ui-ux-pro-max` for design decisions and
  `frontend-ui-engineering` for spacing tokens and build standards; this skill audits and repairs the
  mechanics and defers to the brand where the two disagree.
- It does not replace real-device testing. Chrome emulation proves layout after a resize, not Safari
  behaviour (dynamic toolbar, rubber-band scroll, keyboard insets) nor how a page feels on a 32-inch
  display. When either matters and you have not tested it, say **unverified** in one line — never imply
  emulation is the device.
- It does not touch content, copy, or art direction while fixing layout. If a fix would change what the
  page says, stop and ask.

## Pitfalls that cause false passes

- **Building the summary table by hand.** Every row of a findings table comes from the run's JSON, generated,
  never typed: on 2026-10-22 a hand-written row called a site clean while that site's own JSON flagged a
  squashed logo and a 14 px input on the same widths. Re-measured live the next hour, the row was wrong and the
  JSON was right. If a row and the JSON disagree, the JSON is the finding.
- Measuring before fonts and images settle: scroll first, wait, then measure.
- Testing only phone widths. Half the failure modes live above 1440 px.
- Treating `max-width` as inherently good: a 1200 px ceiling on a 3440 px display throws away the screen.
  Tie the ceiling to content type — prose is narrow, catalogues and dashboards are not.
- Testing inside a scaled iframe or the dev-server overlay, which hides real overflow.
- Judging a `position: fixed` header as fine when it covers 30% of a 390 px screen — check viewport
  coverage per width, not only horizontal overflow.
- Assuming `overflow-x: hidden` on `body` is a fix. It hides the symptom and clips content users needed.
- Declaring a component responsive because its container is — audit it at the narrowest **and** widest
  width it is ever rendered in.
- Treating a green gate as done. Passing is the floor: the page can be technically clean and still be the
  weaker version of itself. Report the ceiling gap, never just the checkbox.
