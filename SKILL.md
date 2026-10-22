---
name: responsive-audit
description: Use when auditing or fixing an app's responsiveness.
version: 1.2.0
author: Lareesa Hu (Pulse Branding), built with Hermes
license: Proprietary
metadata:
  hermes:
    icon: lucide:smartphone
    tags:
    - Frontend
    - Responsive
    - Mobile
    - Audit
---

# Responsive audit

A layout is responsive when it can be squeezed to **320 CSS pixels** and stretched to a wall
without losing content, function or legibility. Not when it has breakpoints.

## When to Use

Load this skill when any of these is true:

- Someone says the app or page is broken, cramped, cut off, or "weird on mobile" / "on my phone" /
  "on iPhone".
- A UI change is about to ship and layout must be checked at phone, tablet and desktop widths.
- A new page, component, modal, table, nav or form is being added and its narrow-width behaviour is
  undefined.
- The user asks for a responsive, mobile, breakpoint, viewport, or device-compatibility review.
- A build runs in a desktop shell (Electron, tab, split view) that can be narrowed to phone width.

Do not load it for pure visual/style direction (use `ui-ux-pro-max`) or for spacing and build standards
(use `frontend-ui-engineering`).

## The foundational principle

> **Responsive layout is the absence of fixed constraints, not the presence of breakpoints.**
> Every dimension is either intrinsic (content decides), relative (`%`, `fr`, `vw` inside `clamp()`),
> or bounded (`min()` / `max()`). Any hard `width`, `min-width`, `height`, or absolutely positioned
> column is a decision that the layout must eventually break at some width.

Three consequences, and every rule in this skill falls out of them:

1. **Width belongs to the content**, so shrinking removes width, never content. There are exactly four
   sanctioned narrow-width behaviours: **reflow** (stack), **scroll inside its own container**, **shrink
   to a floor**, or **replace with a compact variant**. A fifth behaviour — silently clipping, hiding, or
   overflowing the page — is a bug, always.
2. **The narrowest real target is the constraint**, so build down from 320 px, not down from a desktop
   screenshot. WCAG 2.2 SC 1.4.10 requires no two-dimensional scrolling at 320 CSS px (= 1280 px at 400%
   zoom). Anything that fails at 320 is broken for a real iPhone SE in landscape zoom.
3. **Legibility and touch have floors that layout may not cross**: body text ≥ 16 px on phones, form
   inputs ≥ 16 px (below that iOS Safari zooms on focus), interactive targets ≥ 44 × 44 px (Apple HIG) and
   never below 24 × 24 px (WCAG 2.5.8).

Device lists are a checklist of *places to look*, never the design target. If the layout is correct by
construction, every width between 320 and 2560 passes without a new breakpoint.

## Workflow

Public source of this skill: <https://github.com/lareesahu/responsive-audit> (MIT). If the local copy and
the repo disagree, the repo is canonical — pull it rather than editing a stale copy.

### 1. Establish the target
Name the app, the URL or file, the build (branch/commit or port), and the viewport ladder you will test.
Read the project's own conventions first (`AGENTS.md`, design tokens, existing breakpoints) so fixes reuse
the house scale instead of inventing values. Default ladder is in `references/device-ladder.md`.

### 2. Run the measurable audit

```bash
python scripts/responsive_audit.py --url http://127.0.0.1:5173 --out ./audit
```

It loads the page at every width in the ladder, scrolls it to trigger lazy content, then traces real
geometry: horizontal overflow and which element causes it, text clipped by fixed heights, targets under
44 px, inputs that trigger iOS zoom, images distorted by `object-fit: fill`, and tiny type. It writes
screenshots plus a JSON report and exits non-zero when the gate fails.

Never substitute "I looked at a screenshot" for this run. Screenshots prove appearance; the script proves
geometry.

What the script treats as a hard failure: page overflow wider than 1 px, a layout viewport that had to
widen to fit fixed-width content, text clipped by a fixed height, an input under 16 px at phone widths
(iOS zoom), an image squashed by more than 8%, a touch target under 24 px, and a missing
`width=device-width` viewport tag. What it reports as advisory only: targets under 44 px, type under 12 px,
and fixed chrome covering more than 35% of the screen. Advisory findings still belong in the report — they
are just not the same as broken. Links inside a sentence are exempt from the target rules, as WCAG 2.5.8
exempts them.

### 3. Classify, then fix by pattern
Each finding belongs to one of five classes. Fix the class, not the instance — one fixed `width` usually
means eight more like it, and patching only the one you saw is how a page passes today and breaks next week.

| Class | Symptom | Fix pattern |
|---|---|---|
| Fixed dimension | `scrollWidth > innerWidth`, element crossing the right edge | Replace `width`/`min-width` with `max-width` + `%`, `minmax()`, `flex: 1 1 auto`, or `clamp()` |
| Rigid row | Side-by-side blocks that cannot fit | `grid-template-columns: repeat(auto-fit, minmax(240px, 1fr))` or `flex-wrap: wrap`; stack under 640 px |
| Clipped content | Text cut, truncation with no alternative | Remove fixed `height`, use `min-height`; allow wrap; if truncation is intended, give a real disclosure |
| Touch/type floor | Target < 44 px, input < 16 px, body < 16 px | Pad the hit area (never the visual), set `font-size: max(16px, 1rem)` on inputs |
| Viewport unit abuse | Elements jump with the iOS URL bar, content behind the home indicator | `100dvh`/`100svh` instead of `100vh`; `padding-bottom: env(safe-area-inset-bottom)`; `viewport-fit=cover` |

`references/fix-patterns.md` holds the exact CSS for each, and `references/ios-checklist.md` holds the
iOS-specific traps (zoom-on-focus, safe areas, sticky bars, hover-only affordances, momentum scroll).

### 4. Verify, then report
Re-run the script until every width passes, then look at the four screenshots that matter (320, 390, 768,
1440) with your own eyes before claiming anything. A passing script with an ugly phone layout is a fail —
geometry is the floor, not the standard.

Report as: what failed, what class it belonged to, what changed, and the gate line
`Responsive gate: 320 ✓ 375 ✓ 390 ✓ 430 ✓ 768 ✓ 1024 ✓ 1440 ✓` — or the widths that still fail, named.

## What this skill is not

- It does not choose the visual direction. Load `ui-ux-pro-max` for design decisions and
  `frontend-ui-engineering` for spacing tokens and build standards; this skill audits and repairs the
  mechanics and defers to the brand where the two disagree.
- It does not replace real-device testing. Chrome emulation proves layout, not Safari behaviour (dynamic
  toolbar, rubber-band scroll, keyboard insets, `-webkit-fill-available` quirks). When Safari behaviour
  matters and no device is available, say **unverified on iOS** in one line — never imply emulation is iOS.
- It does not touch content, copy, or art direction while fixing layout. If a fix would change what the
  page says, stop and ask.

## Pitfalls that cause false passes

- Measuring before fonts and images settle: scroll first, wait, then measure.
- Testing inside a scaled iframe or the dev-server overlay, which hides real overflow.
- Judging a `position: fixed` header as fine when it covers 30% of a 390 px screen — check viewport
  coverage per width, not only horizontal overflow.
- Assuming `overflow-x: hidden` on `body` is a fix. It hides the symptom and clips content that users
  needed; find the offender and fix it.
- Declaring a component responsive because its container is — the component inherits width, so it must be
  audited at the narrowest width it is ever rendered in.
